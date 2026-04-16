"""Abstract base class for the patient notification system (Observer pattern)."""

from abc import ABC, abstractmethod

from src.models.domain import PatientResponse


class BaseNotifier(ABC):  # pylint: disable=too-few-public-methods
    """
    Observer base class for the patient notification system.

    Each concrete notifier represents one notification channel (email, SMS, push, etc.).
    The PatientService holds a list of BaseNotifier instances and calls notify() on each
    one after a patient is successfully registered.

    To add a new notifier:
        1. Create a new file under src/notifiers/.
        2. Subclass BaseNotifier and implement the notify() method.
        3. Add an instance of your notifier to the list returned by
           get_notifiers() in src/core/dependencies.py.
    """

    @abstractmethod
    async def notify(self, patient: PatientResponse) -> None:
        """Send a notification for the newly registered patient."""
