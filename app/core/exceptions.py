class ServiceException(Exception):
    status_code = 400
    code = "BAD_REQUEST"
    detail = "An error occurred"

    def __init__(self, detail: str | None = None):
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class UserNotFoundError(ServiceException):
    status_code = 404
    code = "USER_NOT_FOUND"
    detail = "User not found"


class UsernameExistsError(ServiceException):
    status_code = 400
    code = "USERNAME_EXISTS"
    detail = "Username already exists"


class InvalidCredentialsError(ServiceException):
    status_code = 401
    code = "INVALID_CREDENTIALS"
    detail = "Invalid credentials"


