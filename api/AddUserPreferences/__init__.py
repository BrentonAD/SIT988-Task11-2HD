import logging
import azure.functions as func

def main(req: func.HttpRequest, preferences: func.Out[func.SqlRow]) -> func.HttpResponse:
    logging.info('Python HTTP trigger and SQL output binding function processed a request.')

    try:
        req_body = req.get_json()
        rows = func.SqlRowList(map(lambda r: func.SqlRow.from_dict(r), req_body))
    except ValueError:
        pass

    if req_body:
        preferences.set(rows)
        return func.HttpResponse(
            body=req.get_body(),
            status_code=201,
            mimetype="application/json"
        )
    else:
        return func.HttpResponse(
            "Error accessing request body",
            status_code=400
        )