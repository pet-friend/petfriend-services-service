from fastapi import HTTPException, status

from app.exceptions.appointments import (
    AppointmentNotFound,
    AppointmentSlotsCantOverlap,
    InvalidAppointment,
)


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

APPOINTMENT_SLOTS_CANT_OVERLAP_ERROR = (
    AppointmentSlotsCantOverlap,
    HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="The appointment slots can't overlap",
    ),
)
