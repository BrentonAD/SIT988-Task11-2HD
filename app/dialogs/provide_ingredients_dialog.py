from botbuilder.dialogs import (
    ComponentDialog,
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
)
from botbuilder.dialogs.prompts import (
    AttachmentPrompt,
    ConfirmPrompt,
    PromptOptions,
    PromptValidatorContext
)
from botbuilder.core import MessageFactory, UserState, ConversationState

from data_models import UserProfile
from ai import TextAnalytics, ImageAnalytics

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
        self.add_dialog(
            AttachmentPrompt(
                AttachmentPrompt.__name__,
                ProvideIngredientsDialog.attachment_prompt_validator
            )
        )
        self.initial_dialog_id = WaterfallDialog.__name__

    async def ingredients_step(
            self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        prompt_options = PromptOptions(
            prompt=MessageFactory.text(
                 "Please provide the ingredients you have on hand. "
                 "This can be as text or in a photo."
            ),
            retry_prompt=MessageFactory.text(
                "The attachment must be a jpeg/png image file."
            )
        )
        return await step_context.prompt(
            AttachmentPrompt.__name__,
            prompt_options
        )
    
    async def handle_ingredients_step(
            self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        # If the return type is a string:
        if isinstance(step_context.result,str):
            raw_ingredients = step_context.result
            text_analytics = TextAnalytics()
            ingredients = text_analytics.key_phrase_extraction([raw_ingredients])
        else:
            attachments = step_context.result
            image_analytics = ImageAnalytics()
            ingredients = image_analytics.detect_objects_in_attachments(attachments)

        if len(ingredients)==0:
            await step_context.context.send_activity(
                    f"I'm sorry I couldn't understand those ingredients, may you please try again?"
                )
            return await step_context.replace_dialog(
                ProvideIngredientsDialog.__name__
            )

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
            if len(allergy_notice)>0:
                if len(ingredients_ammended)>1:
                    ingredients_msg = ", ".join(ingredients_ammended[:-1]) + ", and " + ingredients_ammended[-1]
                else:
                    ingredients_msg = ingredients_ammended[0]   
                if len(allergy_notice)>1:
                    allergy_notice_msg = ", ".join(allergy_notice[:-1]) + ", and " + allergy_notice[-1]
                else:
                    allergy_notice_msg = allergy_notice[0]            
                allergy_msg = f"""
                    Please note I have filtered out {allergy_notice_msg}
                    because you have previously said you are allergic."""
            else:
                ingredients = ingredients_ammended
                allergy_msg = ""
        else:
            allergy_msg = ""

        if len(ingredients)>1:
            ingredients_msg = ", ".join(ingredients[:-1]) + ", and " + ingredients[-1]
        else:
            ingredients_msg = ingredients[0]
        msg = f"From what I understood you currently have {ingredients_msg} on hand?" + allergy_msg

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

    @staticmethod
    async def attachment_prompt_validator(prompt_context: PromptValidatorContext) -> bool:
        if not prompt_context.recognized.succeeded:
            prompt_context.recognized.value = prompt_context.context.activity.text
            return True
        
        attachments = prompt_context.recognized.value

        valid_images = [
            attachment
            for attachment in attachments
            if attachment.content_type in ["image/jpeg","image/png"]
        ]

        prompt_context.recognized.value = valid_images

        return len(valid_images) > 0