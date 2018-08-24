from pystache import Renderer
import os
import base64

    
escape = lambda x: x
renderer = Renderer(escape=escape)

context = {}
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ico.sol")) as contract_tmpl:
    context['TEMPLATE'] = base64.b64encode(str.encode(contract_tmpl.read()))

constructor = ""
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "constructor.py")) as constructor_tmpl:
    constructor = constructor_tmpl.read()

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "final_contructor.py"), "w") as out:
    print(renderer.render(constructor, context))
