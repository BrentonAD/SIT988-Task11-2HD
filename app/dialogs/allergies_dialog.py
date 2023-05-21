from botbuilder.dialogs import (
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
    ComponentDialog,
)

from botbuilder.dialogs.prompts import TextPrompt, ConfirmPrompt, PromptOptions
from botbuilder.core import MessageFactory

class AllergiesDialog(ComponentDialog):
    def __init__(self, dialog_id: str = None):
        super(AllergiesDialog, self).__init__(
            dialog_id or AllergiesDialog.__name__
        )

        self.add_dialog(
            WaterfallDialog(
                WaterfallDialog.__name__, [self.provide_allergies_step, self.confirm_step, self.loop_step]
            )
        )

        self.initial_dialog_id = WaterfallDialog.__name__
    
    async def provide_allergies_step(
            self, step_context: WaterfallStepContext
        ) -> DialogTurnResult:
        
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Please provide the foods you are allergic to.")),
        )

    async def confirm_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        
        raw_allergies = step_context.result

        # Extract allergies from the text
        allergies = raw_allergies.split(",")
        step_context.values["allergies"] = allergies

        msg = f"From what I understood your allergies are {', '.join(allergies)}. Is this correct?"
        return await step_context.prompt(
            ConfirmPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(msg)),
        )
    
    async def loop_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if step_context.result:
            return await step_context.end_dialog(step_context.values["allergies"])
        else:
            return await step_context.replace_dialog(
                AllergiesDialog.__name__
            )
