from botbuilder.dialogs import (
    ComponentDialog,
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
)
from botbuilder.dialogs.prompts import (
    TextPrompt,
    ConfirmPrompt,
    PromptOptions
)
from botbuilder.core import MessageFactory, UserState, ConversationState

from data_models import UserProfile, ConversationData
from dialogs import AllergiesDialog
from api.request_handler import add_or_update_user, add_user_allergies

class WelcomeNewUserDialog(ComponentDialog):
    def __init__(self, user_state: UserState, conversation_state: ConversationState):
        super(WelcomeNewUserDialog, self).__init__(WelcomeNewUserDialog.__name__)

        self.user_profile_accessor = user_state.create_property("UserProfile")
        self.conversation_data_accessor = conversation_state.create_property("ConversationData")

        self.add_dialog(
            WaterfallDialog(
                WaterfallDialog.__name__,
                [
                    self.tracking_permission_step,
                    self.confirm_tracking_permission_step,
                    self.allergies_step,
                    self.summary_step
                ],
            )
        )
        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(AllergiesDialog(AllergiesDialog.__name__))
        self.initial_dialog_id = WaterfallDialog.__name__

    async def tracking_permission_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        # WaterfallStep always finishes with the end of the Waterfall or with another dialog;
        # here it is a Prompt Dialog. Running a prompt here means the next WaterfallStep will
        # be run when the users response is received.
        
        await step_context.context.send_activity(
            MessageFactory.text(
            "Before we get started, please answer the following question..."
            )
        )

        return await step_context.prompt(
            ConfirmPrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text(
                    "Do you consent to your name, allergies, and recipe preferences being tracked?"
                    "This will help tailor your experiences in the future."
                )
            )
        )
    
    async def confirm_tracking_permission_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        user_profile = await self.user_profile_accessor.get(
            step_context.context, UserProfile
        )
        if step_context.result:
            user_profile.allow_tracking = True
            add_or_update_user(user_profile.id, user_profile.name)
            await step_context.context.send_activity(
                    f"Okay {user_profile.name}, your preferences will be tracked for future use!"
                )
        else:
            await step_context.context.send_activity(
                f"Okay {user_profile.name}, your preferences will not be tracked beyond this conversation."
            )
        return await step_context.prompt(
            ConfirmPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Do you have any food allergies?")),
        )
                
    async def allergies_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if step_context.result:
            return await step_context.begin_dialog(AllergiesDialog.__name__)
        else:
            return await step_context.next(None)

    async def summary_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        # Get the current profile object from user state.  Changes to it
        # will saved during Bot.on_turn.
        user_profile = await self.user_profile_accessor.get(
            step_context.context, UserProfile
        )
        conversation_data = await self.conversation_data_accessor.get(
            step_context.context, ConversationData
        )
        
        user_profile.allergies = step_context.result
        if step_context.result and user_profile.allow_tracking:
            add_user_allergies(user_profile.id, step_context.result)
        conversation_data.did_welcome = True
        await step_context.context.send_activity(
            f"Thank you for providing this information. Now it's time to generate some delicious recipes!"
        )

        # WaterfallStep always finishes with the end of the Waterfall or with another
        # dialog, here it is the end.
        return await step_context.end_dialog()