class ValidationUtils:

    @staticmethod
    def validate_json_structure(data: dict, required_keys: list) -> bool:

        if not isinstance(data, dict):
            return False

        missing_keys = [key for key in required_keys if key not in data]

        if missing_keys:
            print(f"Missing keys: {missing_keys}")
            return False

        return True