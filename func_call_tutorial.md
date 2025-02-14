Skip to main content
Gemini API
Models

Solutions
Code assistance
Showcase
Community
Search
/

English
Sign in
Gemini API docs
API Reference
SDKs
Pricing
Cookbook

Gemini 2.0 Flash is now production ready! Learn more
Home
Gemini API
Models
Was this helpful?

Send feedbackFunction calling tutorial

Python Node.js Go Dart (Flutter) Android Swift Web REST

Function calling makes it easier for you to get structured data outputs from generative models. You can then use these outputs to call other APIs and return the relevant response data to the model. In other words, function calling helps you connect generative models to external systems so that the generated content includes the most up-to-date and accurate information.

You can provide Gemini models with descriptions of functions. These are functions that you write in the language of your app (that is, they're not Google Cloud Functions). The model may ask you to call a function and send back the result to help the model handle your query.

If you haven't already, check out the Introduction to function calling to learn more. You can also try out this feature in Google Colab or view the example code in the Gemini API Cookbook repository.

Example API for lighting control
Imagine you have a basic lighting control system with an application programming interface (API) and you want to allow users to control the lights through simple text requests. You can use the Function Calling feature to interpret lighting change requests from users and translate them into API calls to set the lighting values. This hypothetical lighting control system lets you control the brightness of the light and its color temperature, defined as two separate parameters:

Parameter	Type	Required	Description
brightness	number	yes	Light level from 0 to 100. Zero is off and 100 is full brightness.
colorTemperature	string	yes	Color temperature of the light fixture which can be daylight, cool or warm.
For simplicity, this imaginary lighting system only has one light, so the user does not have to specify a room or location. Here is an example JSON request you could send to the lighting control API to change the light level to 50% using the daylight color temperature:


{
  "brightness": "50",
  "colorTemperature": "daylight"
}
This tutorial shows you how to set up a Function Call for the Gemini API to interpret users lighting requests and map them to API settings to control a light's brightness and color temperature values.

Before you begin: Set up your project and API key
Before calling the Gemini API, you need to set up your project and configure your API key.

 Expand to view how to set up your project and API key

Define an API function
Create a function that makes an API request. This function should be defined within the code of your application, but could call services or APIs outside of your application. The Gemini API does not call this function directly, so you can control how and when this function is executed through your application code. For demonstration purposes, this tutorial defines a mock API function that just returns the requested lighting values:


def set_light_values(brightness: int, color_temp: str) -> dict[str, int | str]:
    """Set the brightness and color temperature of a room light. (mock API).

    Args:
        brightness: Light level from 0 to 100. Zero is off and 100 is full brightness
        color_temp: Color temperature of the light fixture, which can be `daylight`, `cool` or `warm`.

    Returns:
        A dictionary containing the set brightness and color temperature.
    """
    return {
        "brightness": brightness,
        "colorTemperature": color_temp
    }
When you create a function to be used in a function call by the model, you should include as much detail as possible in the function and parameter descriptions. The generative model uses this information to determine which function to select and how to provide values for the parameters in the function call.

Caution: For any production application, you should validate the data being passed to the API function from the model before executing the function.
Note: For programming languages other than Python, you must create a separate function declaration for your API. See the other language programming tutorials for more details.
Declare functions during model initialization
When you want to use function calling, you define the functions as tools in the GenerateContentConfig, along with other generation-related settings (such as temperature or stop tokens).


from google.genai import types

config = types.GenerateContentConfig(tools=[set_light_values])
This can be also be defined as a Python dictionary.


config = {
    'tools': [set_light_values],
}
Generate a function call
Once you have defined your function declarations, you can prompt the model to use the function. You can generate content directly, or using the chat interface.


from google import genai

client = genai.Client()

# Generate directly with generate_content.
response = client.models.generate_content(
    model='gemini-2.0-flash',
    config=config,
    contents='Turn the lights down to a romantic level'
)
print(response.text)

# Use the chat interface.
chat = client.chats.create(model='gemini-2.0-flash', config=config)
response = chat.send_message('Turn the lights down to a romantic level')
print(response.text)
In the Python SDK, functions are called automatically. If you want to handle each function call, or perform some other logic between calls, you can disable it through the flag in the generation config.


from google.genai import types

# Use strong types.
config = types.GenerateContentConfig(
    tools=[set_light_values],
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
)

# Use a dictionary.
config = {
    'tools': [set_light_values],
    'automatic_function_calling': {'disable': True},
}
Parallel function calling
In addition to basic function calling described above, you can also call multiple functions in a single turn. This section shows an example for how you can use parallel function calling.

Define the tools.


def power_disco_ball(power: bool) -> bool:
    """Powers the spinning disco ball."""
    print(f"Disco ball is {'spinning!' if power else 'stopped.'}")
    return True


def start_music(energetic: bool, loud: bool) -> str:
    """Play some music matching the specified parameters.

    Args:
      energetic: Whether the music is energetic or not.
      loud: Whether the music is loud or not.

    Returns: The name of the song being played.
    """
    print(f"Starting music! {energetic=} {loud=}")
    return "Never gonna give you up."


def dim_lights(brightness: float) -> bool:
    """Dim the lights.

    Args:
      brightness: The brightness of the lights, 0.0 is off, 1.0 is full.
    """
    print(f"Lights are now set to {brightness:.0%}")
    return True
Now call the model with an instruction that could use all of the specified tools. This example uses a tool_config, to learn more you can read about configuring function calling.


# Set the model up with tools.
house_fns = [power_disco_ball, start_music, dim_lights]

config = {
    # Set the available functions.
    'tools': house_fns,
    # Disable AFC so you can inspect the results first.
    'automatic_function_calling': {'disable': True},
    # Force the model to act (call 'any' function), instead of chatting.
    'tool_config': {
        'function_calling_config': {
            'mode': 'any'
        }
    }
}

# Call the API.
chat = client.chats.create(model='gemini-2.0-flash', config=config)
response = chat.send_message('Turn this place into a party!')

# Print out each of the function calls requested from this single call.
for fn in response.function_calls:
  args = ", ".join(f"{key}={val}" for key, val in fn.args.items())
  print(f"{fn.name}({args})")

power_disco_ball(power=True)
start_music(energetic=True, loud=True)
dim_lights(brightness=0.3)
Each of the printed results reflects a single function call that the model has requested. To send the results back, include the responses in the same order as they were requested.

The simplest way to do this is by leaving automatic_function_calling enabled, so that the SDK will handle the function calls and response passing automatically.

Note: When using automatic_function_calling with multiple functions, if any of them fail, the SDK will pass the error back to the model where it may be invoked again. This is helpful, for example, if the model has generated an incorrect argument set that can be correct, but may be problematic if your function produces side-effects before an error is raised.

config = {
    'tools': house_fns,
}

# Call the API.
chat = client.chats.create(model='gemini-2.0-flash', config=config)
response = chat.send_message('Do everything you need to this place into party!')

print(response.text)

Disco ball is spinning!
Starting music! energetic=True loud=True
Lights are now set to 50%
Alright, I've turned on the disco ball, started playing "Never gonna give you up.", and dimmed the lights. Let's get this party started!
Function call data type mapping
Automatic schema extraction from Python functions doesn't work in all cases. For example: it doesn't handle cases where you describe the fields of a nested dictionary-object, but the API does support this. The API is able to describe any of the following types:


AllowedType = (int | float | bool | str | list['AllowedType'] | dict[str, AllowedType])
Important: The SDK converts function parameter type annotations to a format the API understands (genai.types.FunctionDeclaration). The API only supports a limited selection of parameter types, and the Python SDK's automatic conversion only supports a subset of that: AllowedTypes = int | float | bool | str | list['AllowedTypes'] | dict
To see what the inferred schema looks like, you can convert it using from_callable:


from pprint import pprint

def multiply(a: float, b: float):
    """Returns a * b."""
    return a * b

fn_decl = types.FunctionDeclaration.from_callable(callable=multiply, client=client)

# to_json_dict() provides a clean JSON representation.
pprint(fn_decl.to_json_dict())

{'description': 'Returns a * b.',
 'name': 'multiply',
 'parameters': {'properties': {'a': {'type': 'NUMBER'},
                               'b': {'type': 'NUMBER'}},
                'type': 'OBJECT'}}
These JSON fields map to the equivalent fields on the Pydantic schema, and can be wrapped as a Tool.


config = types.GenerateContentConfig(
    tools=[types.Tool(function_declarations=[fn_decl])]
)
Here is a declaration for the same multiply function written using the genai.types classes. Note that these classes just describe the function for the API, they don't include an implementation of it, so this approach doesn't work with automatic function calling. However, it does allow you to define functions that aren't concrete Python functions (for example, to wrap a remote HTTP call), and gives you more control between function calls (for example, to change function_calling_config to follow a state graph).


tool = types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="multiply",
        description="Returns a * b.",
        parameters=types.Schema(
            properties={
                'a': types.Schema(type='NUMBER'),
                'b': types.Schema(type='NUMBER'),
            },
            type='OBJECT',
        ),
    )
])
assert tool.function_declarations[0] == fn_decl
Was this helpful?

Send feedback
Except as otherwise noted, the content of this page is licensed under the Creative Commons Attribution 4.0 License, and code samples are licensed under the Apache 2.0 License. For details, see the Google Developers Site Policies. Java is a registered trademark of Oracle and/or its affiliates.

Last updated 2025-02-12 UTC.

Terms
Privacy

English
The new page has loaded..