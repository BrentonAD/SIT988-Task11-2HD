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

from dialogs import ChooseRecipeDialog
from data_models import UserProfile
from ai import TextAnalytics, ImageAnalytics, RecipeGenerator

from api.request_handler import add_user_preferences

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
                    self.loop_step,
                    self.recipe_generation_step,
                    self.start_over_step,
                    self.final_step
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
        self.add_dialog(ChooseRecipeDialog(ChooseRecipeDialog.__name__))
        self.initial_dialog_id = WaterfallDialog.__name__

    async def ingredients_step(
            self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        prompt_options = PromptOptions(
            prompt=MessageFactory.text(
                 "Please provide the ingredients you have on hand. "
                 "This can be as text or in a photo.\n"
                 "If you provide an image, it will be stored anonymously "
                 "to help improve our services in the future."
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

        if ingredients is None:
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

        step_context.values["ingredients"] = ingredients
        
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
                    "That's great! Let's see what you could make with that...\n"
                    "Remember the recipes generated here are only a guide made by AI. "
                    "Caution should be applied when cooking them. "
                    "Please consult a cooking professional if you are unsure."
                )            
            return await step_context.next(None)
        else:
            await step_context.context.send_activity(
                    f"I'm sorry about that, please try again with a different input."
                )
            return await step_context.replace_dialog(
                ProvideIngredientsDialog.__name__
            )

    async def recipe_generation_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        recipe_generator = RecipeGenerator()
        generated_recipes = recipe_generator.generation_function(step_context.values["ingredients"])
        
        user_profile = await self.user_profile_accessor.get(
            step_context.context, UserProfile
        )
        # Filter allergies out of recipes
        if user_profile.allergies:
            generated_recipes = [ 
                text for text in generated_recipes
                    if not any(allergy in text for allergy in user_profile.allergies)
                ]

        step_context.values["recipes"] = generated_recipes

        for text in generated_recipes:
            section_msg = ""
            sections = text.split("\n")
            for section in sections:
                section = section.strip()
                if section.startswith("title:"):
                    section = section.replace("title:", "")
                    headline = "TITLE"
                elif section.startswith("ingredients:"):
                    section = section.replace("ingredients:", "")
                    headline = "INGREDIENTS"
                elif section.startswith("directions:"):
                    section = section.replace("directions:", "")
                    headline = "DIRECTIONS"
                
                if headline == "TITLE":
                    section_msg += f"[{headline}]: {section.strip().capitalize()}\n\n"
                else:
                    section_info = [f"  - {i+1}: {info.strip().capitalize()}" for i, info in enumerate(section.split("--"))]
                    section_msg += f"[{headline}]\n\n"
                    section_msg += "\n\n".join(section_info)+"\n\n"
            await step_context.context.send_activity(
                MessageFactory.text(section_msg)
            )
        if user_profile.allow_tracking:
            return await step_context.begin_dialog(ChooseRecipeDialog.__name__, {"selected": [], "recipes": generated_recipes})
        else:
            return await step_context.next(None)
    
    async def start_over_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        # If the user had selected preferences because they allowed tracking, add to the database
        if step_context.result:
            user_profile = await self.user_profile_accessor.get(
                step_context.context, UserProfile
            )
            preferences = [ 
                {"recipe" : recipe, "marked_as_preference": (idx in step_context.result)}
                    for idx, recipe in enumerate(step_context.values["recipes"])
                ]
            add_user_preferences(user_profile.id, preferences)

        msg = "Thank you for participating. Would you like to try some more ingredients?"
        return await step_context.prompt(
            ConfirmPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(msg)),
        )

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if step_context.result:
            await step_context.context.send_activity(
                    f"Okay, no problem!"
                )            
            return await step_context.replace_dialog(
                ProvideIngredientsDialog.__name__
            )
        else:
            await step_context.context.send_activity(
                    f"That's okay, send me another message if you would like to generate another recipe."
                )
            return await step_context.end_dialog(
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