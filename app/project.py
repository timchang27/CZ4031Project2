from flask import Flask, request, render_template
from preprocessing import get_plans
import logging
import json

app = Flask(__name__)


@app.after_request
def add_header(response):
    response.headers["X-UA-Compatible"] = "IE=Edge,chrome=1"
    response.headers["Cache-Control"] = "public, max-age=0"
    return response


@app.route("/", methods=["GET", "POST"])
def index():
    # context for rendering the page
    context = {
        "query1": None,
        "query2": None,
        "errors1": [],
        "errors2": [],
        "plan_data1": None,
        "plan_data2": None,
        "summary_data1": None,
        "summary_data2": None,
        "explanation": None,
    }

    # handle POST request
    if request.method == "POST":
        # get query from the POST request
        query_string = request.form.get("json_data", "")
        query = json.loads(query_string)
        query1 = query["query1"]
        query2 = query["query2"]
        
        if query1:
            context["query1"] = query1

            # get query result
            has_error1, result1 = get_plans(query1)

            # add results to context
            if has_error1:
                context["errors1"].append(result1["msg"])
            else:
                context["summary_data1"] = result1["summary_data"]
                context["plan_data1"] = result1["plan_data"]
                context["natural_explain1"] = result1["natural_explain"]
        else:
            context["errors1"].append("No query provided!")

        if query2:
            context["query2"] = query2

            # get query result
            has_error2, result2 = get_plans(query2)

            # add results to context
            if has_error2:
                context["errors2"].append(result2["msg"])
            else:
                context["summary_data2"] = result2["summary_data"]
                context["plan_data2"] = result2["plan_data"]
                context["natural_explain2"] = result2["natural_explain"]
        else:
            context["errors2"].append("No query provided!")   
        context["explanation"] = "This is a sample message"     

    return render_template("index.html", **context)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(host="0.0.0.0", port=5000, debug=True)

