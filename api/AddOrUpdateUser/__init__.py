import json
import azure.functions as func

def main(req: func.HttpRequest, user: func.Out[func.SqlRow]) -> func.HttpResponse:
    """Upsert the user, which will insert it into the users table if the primary key
    (id) for that person doesn't exist. If it does then update it to have the new properties.
    """

    # Note that this expects the body to be a JSON object which
    # have a property matching each of the columns in the table to upsert to.
    body = json.loads(req.get_body())
    row = func.SqlRow.from_dict(body)
    user.set(row)

    return func.HttpResponse(
        body=req.get_body(),
        status_code=201,
        mimetype="application/json"
    )
    