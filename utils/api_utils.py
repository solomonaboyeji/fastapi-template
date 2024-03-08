from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


# Custom OpenAPI schema extension function


def add_scopes_to_description(route, key, required_scopes):
    route[key][
        "description"
    ] = f"""{route[key]['description']}  <p><br /> This endpoint require the requesting user to have some level of permissions. These scopes must have been assigned to the user during account creation. An admin or privlleged user can update a user's account with the scopes requiired. 
     <p><strong>Required Scopes:</strong>  {', '.join(required_scopes)} </p>
    </p>
    """
    return route


def add_scopes_to_docs(app: FastAPI):

    if not app.openapi_schema:
        openapi_schema = get_openapi(title="FastAPI", version="0.1", routes=app.routes)
        app.openapi_schema = openapi_schema

    for route in app.routes:

        route_path = route.path  # type: ignore
        # simplify operation ids
        route.operation_id = route.name  # type: ignore

        # Check if the application should fail if no description is added to the docs
        if not route.__dict__.get("description", None) and (
            route_path in app.openapi_schema["paths"]
            and not app.openapi_schema["paths"][route_path].get("description", None)
        ):
            raise ValueError(
                f"Each endpoint must have their a description. {route_path}"
            )

        for method_type in list(route.__dict__["methods"]):
            if route_path in app.openapi_schema["paths"]:
                if method_type.lower() in app.openapi_schema["paths"][route_path]:
                    method_data = app.openapi_schema["paths"][route_path][
                        method_type.lower()
                    ]
                    if "security" in method_data:
                        method_security_data = method_data["security"]
                        if method_security_data:
                            oa2pb = [
                                a.get("OAuth2PasswordBearer")
                                for a in method_security_data
                                if a.get("OAuth2PasswordBearer")
                            ]
                            if oa2pb:
                                oa2pb = oa2pb[0]
                                app.openapi_schema["paths"][route_path] = (
                                    add_scopes_to_description(
                                        app.openapi_schema["paths"][route_path],
                                        method_type.lower(),
                                        oa2pb,
                                    )
                                )
