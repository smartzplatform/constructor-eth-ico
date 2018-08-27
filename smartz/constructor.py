from smartz.api.constructor_engine import ConstructorInstance
import re
import base64


def _if(var, default=""): 
    if var == True or (var != False and var != None):        
        return str(default)
    
    return ""

    
    

def render_template(tmpl, fields):
    prefix = False
    lastpos = 0

    context = dict(fields)
    context["_if"] = _if


    exp = re.compile(r"\{\{(.*?)\}\}",  re.MULTILINE | re.DOTALL)

    res = ""
    for match in exp.finditer(tmpl):
        expr = match.group(1)
        
        if prefix == False:
            res = tmpl[0:match.start()]
            prefix = True    
            lastpos = match.start()
        res = res + tmpl[lastpos:match.start()] +  str(eval(expr.strip(), context))
        lastpos = match.end()


    res = res + tmpl[lastpos:]
    return res


class Constructor(ConstructorInstance):

    def get_version(self):
        return {
            "result": "success",
            "version": 1
        }

    def get_params(self):
        json_schema = {
            "type": "object",
            "required": [
                "assertion"
            ],
            "additionalProperties": True,

            "properties": {
                "cap": {
                    "title": "Hard cap",
                    "description": "Maximum eth amount",
                    "type": "number",
                    "minumum": 0,
                    "maximum": 1000000000000000000                    
                },
                "softcap": {
                    "title": "Soft cap",
                    "description": "Maximum eth amount",
                    "type": "number",
                    "minumum": 0,
                    "maximum": 1000000000000000000                    
                },
                "start": {
                    "title": "Start time",
                    "description": "",
                    "$ref": "#/definitions/unixTime",
                },
                "end": {
                    "title": "End time",
                    "description": "",
                    "$ref": "#/definitions/unixTime",
                },
                "wallet": {
                    "title": "Wallet address",
                    "description": "",
                    "$ref": "#/definitions/address"
                },
                "rate": {
                    "title": "Rate",
                    "description": "",
                    "type": "number",
                    "minimum": 0,
                    "maximum": 99999999999999999999,
                },
                "min_contribution": {
                    "title": "Soft cap",
                    "description": "Maximum eth amount",
                    "type": "number",
                    "minumum": 0,
                    "maximum": 100000000000000000000,                             
                },
                "need_burn": {
                    "title": "Burn token after end",
                    "description": "",
                    "type": "boolean",
                },
                "mintable_token": {
                    "title": "Is token mintable",
                    "description": "",
                    "type": "boolean",
                }
            }
        }

        ui_schema = {
            "start": {
                "ui:widget": "unixTime",
            },
            "end": {
                "ui:widget": "unixTime",
            },
            "cap": {
                "ui:widget": "ethCount",
            },
            "softcap": {
                "ui:widget": "ethCount",
            },
            "min_contribution": {
                "ui:widget": "ethCount",
            },
        }

        return {
            "result": "success",
            "schema": json_schema,
            "ui_schema": ui_schema
        }

    def construct(self, fields):  
        context = {}     
        def fill_context(f, default):
            context[f] = fields.get(f, default)

        zeroAddr = 'address(0)'

        fill_context('is_whitelisted', False)
        fill_context('cap', 0)
        fill_context('has_cap_per_person', False)

        fill_context('rate', 1)
        fill_context('wallet', zeroAddr)
        fill_context('token', zeroAddr)
        fill_context('softcap', 0)
        fill_context('min_contribution', 0)
        fill_context('need_burn', False)
        fill_context('start', 'now')
        fill_context('end', 'now + 86400*7')
        fill_context('is_minted_token', False)

        template = base64.b64decode(self.__class__._TEMPLATE).decode('utf-8')

        return {
            "result": "success",
            'source': render_template(template, context),
            'contract_name': "ICO" if not context['is_minted_token'] else "MintedIco"
        }

    def post_construct(self, fields, abi_array):
        function_titles = {}
        def make_title(title, obj):
            function_titles[title] = obj
        if fields.get('is_whitelisted', False):
            make_title('addAddressToWhitelist', {
                'title': 'Add address to whitelist',
                'description': 'Only owner function.',
                'inputs': [
                        {
                            'title': 'Address',
                            'description': 'Whitelisted address'
                        },
                ],
                'sorting_order': 300,
                'icon': {
                        'pack': 'materialdesignicons',
                        'name': 'text'
                },
            })
        
            make_title('addAddressesToWhitelist', {
                'title': 'Add addresses to whitelist',
                'description': 'Only owner function.',
                'inputs': [
                        {
                            'title': 'Addresses',
                            'description': 'Whitelisted addresses'
                        },
                ],
                'sorting_order': 300,
                'icon': {
                        'pack': 'materialdesignicons',
                        'name': 'text'
                },
            })

        make_title("buyTokens", {
            "title": 'Buy tokens',
            'decription': 'Buy tokens for specific address',
            'inputs': [
                {
                    'title': 'Address',
                    'description': ''
                }
            ]}           
        )
        # "cap()": "355274ea",
        # "capReached()": "4f935945",
        # "caps(address)": "66d97b21",
        # "checkRole(address,string)": "0988ca8c",
        # "closingTime()": "4b6753bc",
        # "contributions(address)": "42e94c90",
        # "finalize()": "4bb278f3",
        # "getUserCap(address)": "8b58c64c",
        # "getUserContribution(address)": "bb8b2b47",
        # "hasClosed()": "1515bc2b",
        # "hasRole(address,string)": "217fe6c6",
        # "isFinalized()": "8d4e4083",
        # "openingTime()": "b7a8807c",
        # "owner()": "8da5cb5b",
        # "rate()": "2c4e722e",
        # "removeAddressFromWhitelist(address)": "286dd3f5",
        # "removeAddressesFromWhitelist(address[])": "24953eaa",
        # "renounceOwnership()": "715018a6",
        # "setGroupCap(address[],uint256)": "a31f61fc",
        # "setNextSale(address)": "52d63b7e",
        # "setUserCap(address,uint256)": "c3143fe5",
        # "token()": "fc0c546a",
        # "transferOwnership(address)": "f2fde38b",
        # "wallet()": "521eb273",
        # "weiRaised()": "4042b66f",
        # "whitelist(address)": "9b19251a"

       
        return {
            "result": "success",
            'function_specs': function_titles,
            'dashboard_functions': ['buyTokens']
        }


    # language=Solidity
    _TEMPLATE = """
{{ TEMPLATE }}
    """

    _PAYMENT_CODE="%payment_code%"