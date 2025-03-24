class EventProcessingError(Exception):
    """Base class for event processing errors"""

    def __init__(self, message):
        super().__init__(message)


class EventPublishingError(EventProcessingError):
    """Exception raised when an event fails to be published"""

    def __init__(self, event_type, error):
        super().__init__(f"Error publishing event '{event_type}': {error}")


class EventConsumptionError(EventProcessingError):
    """Exception raised when an error occurs during event consumption"""

    def __init__(self, event_data, error):
        super().__init__(f"Error processing event {event_data}: {error}")
