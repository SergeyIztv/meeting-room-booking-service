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


class PastDateBookingError(ServiceException):
    status_code = 400
    code = "PAST_DATE"
    detail = "Cannot book in the past"


class SlotNotFoundError(ServiceException):
    status_code = 404
    code = "SLOT_NOT_FOUND"
    detail = "Slot not found"


class RoomMismatchError(ServiceException):
    status_code = 404
    code = "ROOM_NOT_FOUND"
    detail = "Room not found or slot mismatch"


class BookingAlreadyExistsError(ServiceException):
    status_code = 409
    code = "SLOT_ALREADY_BOOKED"
    detail = "Этот временной слот уже забронирован."


class BookingNotFoundError(ServiceException):
    status_code = 404
    code = "BOOKING_NOT_FOUND"
    detail = "Booking not found"


class PastBookingCancellationError(ServiceException):
    status_code = 400
    code = "PAST_BOOKING_CANCELLATION"
    detail = "Нельзя отменить бронирование из прошлого."


class CancelForbiddenError(ServiceException):
    status_code = 403
    code = "FORBIDDEN"
    detail = "Cannot cancel another user's booking"


