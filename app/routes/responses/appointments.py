from fastapi import HTTPException, status

from app.exceptions.appointments import AppointmentNotFound, InvalidAppointment


APPOINTMENT_NOT_FOUND_ERROR = (
    AppointmentNotFound,
    HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Appointment not found",
    ),
)

INVALID_APPOINTMENT_ERROR = (
    InvalidAppointment,
    HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="An available appointment for this service at the given start time was not found",
    ),
)
