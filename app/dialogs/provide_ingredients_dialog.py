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

from data_models import UserProfile
from ai import TextAnalytics

class ProvideIngredientsDialog(ComponentDialog):
    
    def __init__(self, user_state: UserState, conversation_state: ConversationState):
        super(ProvideIngredientsDialog, self).__init__(ProvideIngredientsDialog.__name__)

        self.user_profile_accessor = user_state.create_property("UserProfile")
        self.conversation_data_accessor = conversation_state.create_property("ConversationData")

        self.add_dialog(
            WaterfallDialog(
                WaterfallDialog.__name__,
                [
                    self.ingredients_step,
                    self.handle_ingredients_step,
                    self.loop_step
                ],
            )
        )
        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.initial_dialog_id = WaterfallDialog.__name__

    async def ingredients_step(
            self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text(
                    "Please provide the ingredients you have on hand."
                    "This can be as text or in a photo."
                )
            )
        )
    
    async def handle_ingredients_step(
            self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        raw_ingredients = step_context.result
        text_analytics = TextAnalytics()
        ingredients = text_analytics.key_phrase_extraction([raw_ingredients])

        user_profile = await self.user_profile_accessor.get(
            step_context.context, UserProfile
        )
        if user_profile.allergies:
            ingredients_ammended = [
                ingredient for ingredient in ingredients
                    if ingredient not in user_profile.allergies
                ]
            allergy_notice = [
                ingredient for ingredient in ingredients
                    if ingredient in user_profile.allergies
            ]

            if len(ingredients_ammended)>1:
                ingredients_msg = ", ".join(ingredients_ammended[:-1]) + ", and " + ingredients_ammended[-1]
            else:
                ingredients_msg = ingredients_ammended[0]   
            if len(allergy_notice)>1:
                allergy_notice_msg = ", ".join(allergy_notice[:-1]) + ", and " + allergy_notice[-1]
            else:
                allergy_notice_msg = allergy_notice[0]            
            msg = f"""From what I understood you currently have {ingredients_msg} on hand?
                Please note I have filtered out {allergy_notice_msg}
                because you have previously said you are allergic."""
        else:
            if len(ingredients)>1:
                ingredients_msg = ", ".join(ingredients[:-1]) + ", and " + ingredients[-1]
            else:
                ingredients_msg = ingredients[0]
            msg = f"From what I understood you currently have {ingredients_msg} on hand?"

        return await step_context.prompt(
            ConfirmPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(msg)),
        )
        
    async def loop_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if step_context.result:
            await step_context.context.send_activity(
                    f"Thank you"
                )            
            return await step_context.end_dialog(None)
        else:
            await step_context.context.send_activity(
                    f"I'm sorry about that, please try again with a different input."
                )
            return await step_context.replace_dialog(
                ProvideIngredientsDialog.__name__
            )
