import logging
import json
import azure.functions as func

# The input binding executes the `SELECT * FROM users WHERE id = @id` query.
# The Parameters argument passes the `{id}` specified in the URL that triggers the function,
# `users/{id}`, as the value of the `@id` parameter in the query.
# CommandType is set to `Text`, since the constructor argument of the binding is a raw query.
def main(req: func.HttpRequest, allergies: func.SqlRowList) -> func.HttpResponse:
    
    logging.info("Converting the payload to json")
    rows = list(map(lambda r: json.loads(r.to_json()), allergies))

    return func.HttpResponse(
        json.dumps(rows),
        status_code=200,
        mimetype="application/json"
    )