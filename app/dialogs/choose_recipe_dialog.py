from botbuilder.dialogs import (
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
    ComponentDialog,
    PromptOptions
)

from botbuilder.dialogs.choices import Choice, FoundChoice
from botbuilder.dialogs.dialog_context import DialogContext
from botbuilder.dialogs.dialog_turn_result import DialogTurnResult

from botbuilder.dialogs.prompts import ChoicePrompt
from botbuilder.core import MessageFactory

from typing import List

class ChooseRecipeDialog(ComponentDialog):
    def __init__(self, dialog_id: str = None):
        super(ChooseRecipeDialog, self).__init__(
            dialog_id or ChooseRecipeDialog.__name__
        )
        self.add_dialog(ChoicePrompt(ChoicePrompt.__name__))
        self.add_dialog(
            WaterfallDialog(
                WaterfallDialog.__name__, [self.selection_step, self.loop_step]
            )
        )
        self.RECIPES_SELECTED = "value-recipesSelected"
        self.DONE_OPTION = "Done"
        self.initial_dialog_id = WaterfallDialog.__name__
    
    async def selection_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        # step_context.options will contains the value passed in begin_dialog or replace_dialog.
        # if this value wasn't provided then start with an emtpy selection list.  This list will
        # eventually be returned to the parent via end_dialog.
        recipes = step_context.options["recipes"]
        self.recipe_options = [f"Recipe {idx+1}" for idx, _ in enumerate(recipes)]
        selected: List[str] = step_context.options["selected"]
        step_context.values[self.RECIPES_SELECTED] = selected
        if len(selected) == 0:
            message = (
                f"Please choose a recipe to mark as your preference, or `{self.DONE_OPTION}` to finish."+\
                "This will be added to your preferences"
            )
        elif len(selected)<len(recipes):
            message = (
                f"You have selected **{selected[-1]}**. You can review an additional recipe, "
                f"or choose `{self.DONE_OPTION}` to finish. "
            )
        else:
            return await step_context.end_dialog([1]*len(recipes))

        # create a list of options to choose, with already selected items removed.
        options = self.recipe_options.copy()
        options.append(self.DONE_OPTION)
        if len(selected) > 0:
            options = [option for option in options if option not in selected]
        # prompt with the list of choices
        prompt_options = PromptOptions(
            prompt=MessageFactory.text(message),
            retry_prompt=MessageFactory.text("Please choose an option from the list."),
            choices=self._to_choices(options),
        )
        return await step_context.prompt(ChoicePrompt.__name__, prompt_options)

    def _to_choices(self, choices: List[str]) -> List[Choice]:
        choice_list: List[Choice] = []
        for choice in choices:
            choice_list.append(Choice(value=choice))
        return choice_list

    async def loop_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        selected: List[str] = step_context.values[self.RECIPES_SELECTED]
        choice: FoundChoice = step_context.result
        done = choice.value == self.DONE_OPTION

        # If they chose a company, add it to the list.
        if not done:
            selected.append(choice.value)

        # If they're done, exit and return their list.
        if done:
            if len(selected)>0:
                recipes_selected_index = [ int(choice[-1])-1 for choice in selected]
            else:
                recipes_selected_index = []
            return await step_context.end_dialog(recipes_selected_index)

        # Otherwise, repeat this dialog, passing in the selections from this iteration.
        return await step_context.replace_dialog(
            ChooseRecipeDialog.__name__, {"selected":selected, "recipes":step_context.options["recipes"]}
        )
