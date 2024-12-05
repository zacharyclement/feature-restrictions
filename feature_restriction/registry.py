from feature_restriction.event_handlers import (
    ChargebackOccurredHandler,
    CreditCardAddedHandler,
    PurchaseMadeHandler,
    ScamMessageFlaggedHandler,
)
from feature_restriction.rules import (
    ChargebackRatioRule,
    ScamMessageRule,
    UniqueZipCodeRule,
)


class RuleRegistry:
    """
    Manages the registration and retrieval of rules.
    """

    def __init__(self):
        self.rules = {}

    def register_rule(self, rule_instance):
        rule_name = getattr(rule_instance, "name", None)
        if not rule_name:
            raise ValueError(
                f"Rule '{rule_instance.__class__.__name__}' must have a 'name' attribute."
            )
        if rule_name in self.rules:
            raise ValueError(
                f"A rule with the name '{rule_name}' is already registered."
            )
        self.rules[rule_name] = rule_instance

    def get_rule(self, rule_name):
        """
        Retrieve a rule by its name.
        """
        return self.rules.get(rule_name)

    def register_default_rules(self, tripwire_manager, user_manager):
        """
        Register default rules.
        """
        self.register_rule(UniqueZipCodeRule(tripwire_manager, user_manager))
        self.register_rule(ScamMessageRule(tripwire_manager, user_manager))
        self.register_rule(ChargebackRatioRule(tripwire_manager, user_manager))


class EventHandlerRegistry:
    """
    Manages the registration and retrieval of event handlers.
    """

    def __init__(self):
        self.event_handler_registry = {}
        self.event_rules_mapping = {}

    def register_event_handler(self, event_handler_instance, rule_names=None):
        """
        Registers an event handler with an optional list of rule names.

        :param event_handler_instance: The instance of the event handler to register.
        :param rule_names: Optional list of rule names associated with the event.
        :raises ValueError: If the handler does not have an 'event_name' attribute or if the event name is already registered.
        """
        event_name = getattr(event_handler_instance, "event_name", None)
        if not event_name:
            raise ValueError(
                f"Handler '{event_handler_instance.__class__.__name__}' must have 'event_name' attribute."
            )

        # Check for duplicate event name
        if event_name in self.event_handler_registry:
            existing_handler = self.event_handler_registry[
                event_name
            ].__class__.__name__
            raise ValueError(
                f"Duplicate event name detected: '{event_name}' is already registered by handler '{existing_handler}'."
            )

        self.event_handler_registry[event_name] = event_handler_instance
        self.event_rules_mapping[event_name] = rule_names or []

    def get_event_handler(self, event_name):
        return self.event_handler_registry.get(event_name)

    def get_rules_for_event(self, event_name):
        return self.event_rules_mapping.get(event_name, [])

    def register_default_event_handlers(self, tripwire_manager, user_manager):
        """
        Register default event handlers and their associated rules.
        """
        self.register_event_handler(
            CreditCardAddedHandler(tripwire_manager, user_manager),
            rule_names=["unique_zip_code_rule"],
        )
        self.register_event_handler(
            ScamMessageFlaggedHandler(tripwire_manager, user_manager),
            rule_names=["scam_message_rule"],
        )
        self.register_event_handler(
            ChargebackOccurredHandler(tripwire_manager, user_manager),
            rule_names=["chargeback_ratio_rule"],
        )
        self.register_event_handler(
            PurchaseMadeHandler(tripwire_manager, user_manager), rule_names=[]
        )
