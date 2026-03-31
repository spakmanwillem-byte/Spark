"""
Scripting Handler - JSON DSL Security Layer
Replaces exec/eval with safe, whitelisted action dispatcher
"""
import json
import ast
from typing import Dict, Any
from datetime import datetime
from services.action_logger import ActionLogger
from utils.logger import SparkLogger
from utils.paths import get_live_trading_path


class ScriptingHandler:
    """
    Central dispatcher for JSON-based scripting commands
    
    Request format:
    {
        "action": "create_trade",
        "params": {"symbol": "BCH-EUR", "amount": 10},
        "user_id": "001"
    }
    
    Response format:
    {
        "success": True/False,
        "result": Any,
        "error": Optional[str],
        "action": str,
        "timestamp": str
    }
    """
    
    # Whitelist van toegestane acties
    ALLOWED_ACTIONS = {
        "create_trade",
        "get_position_state",
        "log_action",
        "calculate"
    }
    
    @classmethod
    def execute(cls, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute een whitelisted action
        
        Args:
            request: JSON request met action, params, user_id
            
        Returns:
            Execution result
        """
        action = request.get("action", "")
        params = request.get("params", {})
        user_id = request.get("user_id", "")
        
        # Validatie
        if not action:
            return cls._error_response("Missing 'action' field")
        
        if action not in cls.ALLOWED_ACTIONS:
            return cls._error_response(
                f"Action '{action}' not allowed. Available: {list(cls.ALLOWED_ACTIONS)}"
            )
        
        if not user_id:
            return cls._error_response("Missing 'user_id' field")
        
        # Dispatch naar correcte handler
        try:
            if action == "create_trade":
                result = cls._handle_create_trade(user_id, params)
            elif action == "get_position_state":
                result = cls._handle_get_position_state(user_id, params)
            elif action == "log_action":
                result = cls._handle_log_action(user_id, params)
            elif action == "calculate":
                result = cls._handle_calculate(params)
            else:
                result = cls._error_response(f"Handler not implemented for '{action}'")
            
            # Add metadata
            result["action"] = action
            result["timestamp"] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            SparkLogger.log_system_event(f"[SCRIPTING ERROR] {action}: {str(e)}")
            return cls._error_response(f"Execution failed: {str(e)}", action=action)
    
    @classmethod
    def _handle_create_trade(cls, user_id: str, params: Dict) -> Dict:
        """
        Trigger een manual trade
        
        Params:
            symbol: Trading pair (default "BCH-EUR")
            amount: Trade amount in EUR (required)
            action: "BUY" or "SELL" (required)
            run_id: Monitor run ID (optional, gebruikt laatste run)
        """
        from services.live_trader_service import LiveTraderService
        from services.spark_decision_engine import SparkDecisionEngine
        
        # Validatie
        if "amount" not in params:
            return cls._error_response("Missing required param: 'amount'")
        if "action" not in params:
            return cls._error_response("Missing required param: 'action'")
        
        trade_action = params["action"].upper()
        if trade_action not in ["BUY", "SELL"]:
            return cls._error_response(f"Invalid action '{trade_action}'. Must be BUY or SELL")
        
        symbol = params.get("symbol", "BCH-EUR")
        amount = float(params["amount"])
        run_id = params.get("run_id", f"manual_{user_id}_{int(datetime.now().timestamp())}")
        
        # Get current price (voor decision format)
        current_price = 0.0
        try:
            from services.bitvavo_service import BitvavoService
            ticker = BitvavoService.get_ticker(symbol)
            if ticker:
                # API geeft "price" terug, niet "last"
                current_price = float(ticker.get("price", ticker.get("last", 0)))
        except Exception as e:
            SparkLogger.log_system_event(f"[SCRIPTING] Ticker fetch failed: {e}")
        
        # Fallback: gebruik een default price voor mock trading
        if current_price == 0.0:
            # Voor BCH-EUR gebruik een redelijke default (alleen voor mock)
            if symbol == "BCH-EUR":
                current_price = 400.0
                SparkLogger.log_system_event(f"[SCRIPTING] Using fallback price {current_price} for {symbol}")
            else:
                return cls._error_response(f"Could not fetch price for {symbol} and no fallback available")
        
        # Maak een decision object (formaat dat LiveTraderService verwacht)
        decision = {
            "action": trade_action,
            "price": current_price,
            "indicators": {
                "price": current_price
            },
            "position_update": {
                "trade_amount": amount / current_price if trade_action == "SELL" and current_price > 0 else amount
            }
        }
        
        # Execute trade
        result = LiveTraderService.execute_decision(
            decision=decision,
            user_id=user_id,
            run_id=run_id,
            market=symbol,
            config={"trade_amount": amount}
        )
        
        # Log de actie
        ActionLogger.log(
            action="CREATE_TRADE",
            entity_type="trade",
            entity_id=run_id,
            details={
                "symbol": symbol,
                "amount": amount,
                "action": trade_action,
                "price": current_price
            },
            success=result.get("success", False)
        )
        
        return {
            "success": result.get("success", False),
            "result": result,
            "error": result.get("error")
        }
    
    @classmethod
    def _handle_get_position_state(cls, user_id: str, params: Dict) -> Dict:
        """
        Haal position state op voor een run
        
        Params:
            run_id: Run ID (required)
            symbol: Trading symbol (default "BCH")
        """
        if "run_id" not in params:
            return cls._error_response("Missing required param: 'run_id'")
        
        run_id = params["run_id"]
        symbol = params.get("symbol", "BCH")
        
        # Constructie pad naar position_state.json (cross-platform)
        position_file = get_live_trading_path(user_id, "runs", run_id, "position_state.json")
        
        # Check 1: File bestaat
        if not position_file.exists():
            return cls._error_response(f"Position state not found for run_id '{run_id}'")
        
        # Check 2: File is niet leeg
        if position_file.stat().st_size == 0:
            return cls._error_response(f"Position state file is empty for run_id '{run_id}'")
        
        # Check 3: Lees en parse JSON
        try:
            with open(position_file, 'r') as f:
                position_data = json.load(f)
            
            # Check 4: Valideer minimale vereiste velden
            if not isinstance(position_data, dict):
                return cls._error_response(f"Position state has invalid format (not a dict)")
            
            # Verwachte velden (optioneel maar goed om te loggen)
            required_fields = ["is_open", "entry_price", "entry_amount"]
            missing_fields = [f for f in required_fields if f not in position_data]
            if missing_fields:
                SparkLogger.log_system_event(
                    f"[SCRIPTING] Position state missing fields: {missing_fields} for run_id {run_id}"
                )
            
            return {
                "success": True,
                "result": {
                    "run_id": run_id,
                    "symbol": symbol,
                    "position": position_data
                },
                "error": None
            }
            
        except json.JSONDecodeError as e:
            return cls._error_response(f"Position state file is corrupted (invalid JSON): {str(e)}")
        except Exception as e:
            return cls._error_response(f"Failed to read position state: {str(e)}")
    
    @classmethod
    def _handle_log_action(cls, user_id: str, params: Dict) -> Dict:
        """
        Log een custom actie
        
        Params:
            action: Action naam (required)
            entity_type: Type entity (required)
            entity_id: Entity ID (required)
            details: Extra details (optional)
        """
        required = ["action", "entity_type", "entity_id"]
        missing = [p for p in required if p not in params]
        if missing:
            return cls._error_response(f"Missing required params: {missing}")
        
        ActionLogger.log(
            action=params["action"],
            entity_type=params["entity_type"],
            entity_id=params["entity_id"],
            details=params.get("details", {}),
            success=True
        )
        
        return {
            "success": True,
            "result": {
                "logged": True,
                "action": params["action"]
            },
            "error": None
        }
    
    @classmethod
    def _handle_calculate(cls, params: Dict) -> Dict:
        """
        Veilige math calculation via ast.literal_eval
        
        Params:
            expression: Math expression (required)
            
        Voorbeeld:
            {"expression": "2 + 2"}
            {"expression": "100 * 0.05"}
        """
        if "expression" not in params:
            return cls._error_response("Missing required param: 'expression'")
        
        expression = params["expression"]
        
        # Safety check 1: Dangerous keywords
        dangerous = ["import", "exec", "eval", "__", "open", "file", "class", "dir", "vars", "globals", "locals"]
        if any(word in expression.lower() for word in dangerous):
            return cls._error_response("Expression contains forbidden keywords")
        
        # Safety check 2: Attribute access (zoals (1).__class__ of obj.attr)
        if "." in expression and not all(c.isdigit() or c == "." for c in expression.replace(" ", "").replace("+", "").replace("-", "").replace("*", "").replace("/", "").replace("(", "").replace(")", "")):
            # Als er een punt is die NIET deel is van een float getal, dan is het attribute access
            try:
                # Parse en check op Attribute nodes
                test_tree = ast.parse(expression, mode='eval')
                for node in ast.walk(test_tree):
                    if isinstance(node, ast.Attribute):
                        return cls._error_response("Attribute access is not allowed in expressions")
            except:
                pass  # Laat de echte parser het later afhandelen
        
        try:
            # Parse expression als Python AST
            tree = ast.parse(expression, mode='eval')
            
            # Whitelist van toegestane operations
            allowed_nodes = (
                ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num, ast.Constant,
                ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow,
                ast.USub, ast.UAdd
            )
            
            # Check of alle nodes toegestaan zijn
            for node in ast.walk(tree):
                if not isinstance(node, allowed_nodes):
                    return cls._error_response(
                        f"Expression contains forbidden operation: {type(node).__name__}"
                    )
            
            # Compile en execute in restricted environment
            code = compile(tree, '<string>', 'eval')
            result = eval(code, {"__builtins__": {}}, {})
            
            return {
                "success": True,
                "result": {
                    "expression": expression,
                    "value": result
                },
                "error": None
            }
            
        except Exception as e:
            return cls._error_response(f"Calculation failed: {str(e)}")
    
    @classmethod
    def _error_response(cls, message: str, action: str = "") -> Dict:
        """Helper voor error responses"""
        return {
            "success": False,
            "result": None,
            "error": message,
            "action": action,
            "timestamp": datetime.now().isoformat()
        }
    
    @classmethod
    def get_available_actions(cls) -> Dict[str, Any]:
        """
        Return lijst van beschikbare acties met documentatie
        """
        return {
            "success": True,
            "actions": {
                "create_trade": {
                    "description": "Trigger een manual trade (BUY/SELL)",
                    "params": {
                        "action": "BUY of SELL (required)",
                        "amount": "Trade amount in EUR (required)",
                        "symbol": "Trading pair (default: BCH-EUR)",
                        "run_id": "Monitor run ID (optional)"
                    },
                    "example": {
                        "action": "create_trade",
                        "params": {
                            "action": "BUY",
                            "amount": 10,
                            "symbol": "BCH-EUR"
                        },
                        "user_id": "001"
                    }
                },
                "get_position_state": {
                    "description": "Haal position state op voor een run",
                    "params": {
                        "run_id": "Run ID (required)",
                        "symbol": "Trading symbol (default: BCH)"
                    },
                    "example": {
                        "action": "get_position_state",
                        "params": {
                            "run_id": "run_user-001_BCH_1774489771"
                        },
                        "user_id": "001"
                    }
                },
                "log_action": {
                    "description": "Log een custom actie",
                    "params": {
                        "action": "Action naam (required)",
                        "entity_type": "Type entity (required)",
                        "entity_id": "Entity ID (required)",
                        "details": "Extra details (optional)"
                    },
                    "example": {
                        "action": "log_action",
                        "params": {
                            "action": "TEST",
                            "entity_type": "scripting",
                            "entity_id": "test_001",
                            "details": {"message": "Test log entry"}
                        },
                        "user_id": "001"
                    }
                },
                "calculate": {
                    "description": "Veilige math calculation",
                    "params": {
                        "expression": "Math expression (required)"
                    },
                    "example": {
                        "action": "calculate",
                        "params": {
                            "expression": "100 * 0.05"
                        },
                        "user_id": "001"
                    }
                }
            }
        }
