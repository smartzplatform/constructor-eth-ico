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
                "cap", "softcap", "start", "end", "token", "wallet",
            ],
            "additionalProperties": False,
            "properties": {
                "cap": {
                    "title": "Hard cap",
                    "description": "Hard cap in ether",
                    "type": "number",
                    "minumum": 1,                    
                    "maximum": 999999999999999999999999999999999,
                    "default": 100               
                },
                "softcap": {
                    "title": "Soft cap",
                    "description": "Softcap in ether",
                    "type": "number",
                    "minumum": 0,
                    "maximum": 999999999999999999999999999999999,
                    "default": 1
                },
                "min_contribution": {
                    "title": "Minimal contribution",
                    "description": "Minimal contribution per transaction in eth",
                    "type": "number",
                    "minumum": 0,
                    "maximum": 9999999999999999999999999999999999,
                    "default": 0.001                           
                },
                "start": {
                    "title": "Start date",
                    "description": "ICO start date and time (UTC)",
                    "$ref": "#/definitions/unixTime",
                },
                "end": {
                    "title": "End date",
                    "description": "ICO end date and time (UTC)",
                    "$ref": "#/definitions/unixTime",
                },
                "wallet": {
                    "title": "Wallet address",
                    "description": "All collected funds will be transferred to this address",
                    "$ref": "#/definitions/address"
                },
                "token": {
                    "title": "Token address",
                    "description": "Token contract address",
                    "$ref": "#/definitions/address"
                },                
                "rate": {
                    "title": "Rate",
                    "description": "Tokens to issue per 1 Ether",
                    "type": "number",
                    "minimum": 0,
                    "maximum": 9999999999999999999999999999999999,
                    "default": 1
                },              
              
                "limited_contributor_list": {
                    "title": "Limit list of contributors",
                    "description": """Allow only specific contributors. 
                        Whitelist - accept any contribution from whitelisted addresses. 
                        Whitelist with hard cap per user - accept contribution for specific addresses with upper limit.
                        No limits - all contributors allowed.
                    """,
                    "type": "string",
                    "default": 'No limits',
                    "enum": [
                        'Whitelist', 'Whitelist with hard cap per user', 'No limits'
                    ]
                },
                "need_burn": {
                    "title": "Use burnable token",
                    "description": "Burn non distributed tokens after ICO will be successfull completed",
                    "type": "boolean",
                    "default": False
                },
                "mintable_token": {
                    "title": "Use mintable token",
                    "description": "Assume that token has mint method that allow ICO contract create tokens",
                    "type": "boolean",
                    "default": False
                },         
            }
        }

        ui_schema = {
            "limited_contributor_list": {
                "ui:widget": "radio",
            },
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
        contrib_limits = fields.get('limited_contributor_list', 'No limits')
        if contrib_limits == 'Whitelist':
            fields['is_whitelisted'] = True
        elif contrib_limits == 'Whitelist with hard cap per user':
            fields['has_cap_per_person'] = True        
            
        fill_context('is_whitelisted', False)
        fill_context('has_cap_per_person', False)
        fill_context('cap', "0 ether")
        

        fill_context('rate', 1)
        fill_context('wallet', zeroAddr)
        fill_context('token', zeroAddr)
        fill_context('softcap', "1 ether")
        fill_context('min_contribution', "0 ether")
        fill_context('need_burn', False)
        fill_context('start', 'now')
        fill_context('end', 'now + 86400*7')
        fill_context('mintable_token', False)

        template = base64.b64decode(self.__class__._TEMPLATE).decode('utf-8')

        return {
            "result": "success",
            'source': render_template(template, context),
            'contract_name': "ICO" if not context['mintable_token'] else "MintedIco"
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
            'description': 'Buy tokens for specific address',
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