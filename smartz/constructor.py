from smartz.api.constructor_engine import ConstructorInstance
import re
import base64


def _if(var, default=""): 
    if var == True or (var != False and var != None):        
        return str(default)
    
    return ""

def _for(l, f):
    ret = ""
    for e in l:
        ret = ret + f(e) + "\n"
    return ret
    
    

def render_template(tmpl, fields):
    prefix = False
    lastpos = 0

    context = dict(fields)
    context["_if"] = _if
    context["_for"] = _for


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
                "discount_mapping": {
                    "title": "Discount token prices for dates",
                    "description": "Different token rates for each sale period.",
                    "type": "array",
                    "items": 
                        {   
                            "type": "array",
                            "minItems": 2,
                            "maxItems": 2,
                            "items": [
                                {
                                    "title": "Until date",
                                    "$ref": "#/definitions/unixTime"
                                },
                                {
                                    "title": "Rate",
                                    "$ref": "#/definitions/uint256"
                                }
                            ]
                        }                    
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
        def fill_context(f, default, m=lambda e: e):
            if f in fields:
                context[f] = m(fields.get(f))
            else:
                context[f] = default

        zeroAddr = 'address(0)'
        contrib_limits = fields.get('limited_contributor_list', 'No limits')
        if contrib_limits == 'Whitelist':
            fields['is_whitelisted'] = True
        elif contrib_limits == 'Whitelist with hard cap per user':
            fields['has_cap_per_person'] = True        
            
        fill_context('is_whitelisted', False)
        fill_context('has_cap_per_person', False)
        
        fill_context('cap', "0 ether", int)
        

        fill_context('rate', 1)
        fill_context('wallet', zeroAddr)
        fill_context('token', zeroAddr)
        fill_context('softcap', "1 ether", int)
        fill_context('min_contribution', "0 ether", int)
        fill_context('need_burn', False)
        fill_context('start', 'now')
        fill_context('end', 'now + 86400*7')
        fill_context('mintable_token', False)

        context['discount_dates'] = map(lambda e: e[0], fields.get('discount_mapping', []))
        context['discount_rates'] = map(lambda e: e[1], fields.get('discount_mapping', []))

        template = base64.b64decode(self.__class__._TEMPLATE).decode('utf-8')

        return {
            "result": "success",
            'source': render_template(template, context),
            'contract_name': "ICO" if not context['mintable_token'] else "MintedIco"
        }

    def post_construct(self, fields, abi_array):
        function_titles = {}
        contrib_limits = fields.get('limited_contributor_list', 'No limits')
        if contrib_limits == 'Whitelist':
            fields['is_whitelisted'] = True
        elif contrib_limits == 'Whitelist with hard cap per user':
            fields['has_cap_per_person'] = True

        def make_title(title, obj):
            function_titles[title] = obj

          

        make_title('weiRaised', {
            'title': 'Wei raised',
            'description': 'Total amount of collected wei',
            'sorting_order': 10
        })

        make_title('token', {
            'title': 'Token address',
            'description': '',
            'sorting_order': 20
        })
        make_title('owner', {
            'title': 'Contract owner',
            'sorting_order': 30
        })
        
        make_title('rate', {
           'title': 'Base wei to token conversion rate',
            'description': 'How many token units a buyer gets per wei. The rate is the conversion between wei and the smallest and indivisible token unit.',
            'sorting_order': 40
        })

        make_title('getRate', {
            'title': 'Current wei to token conversion rate',
            'description': 'Token rate with possible discount.'
        })


        make_title('wallet', {
            'title': 'Contributions target address',
            'description': 'Address where contributions will be collected',
            'sorting_order': 50
        })


        make_title('cap', {
            'title': 'Hard cap',
            'description': 'Max amount of wei to be contributed',
            'sorting_order': 60
        })
        make_title('cSoftCap', {
            'title': 'Soft cap',
            'sorting_order': 70
        })
        make_title('openingTime', {
            'title': 'Opening time',
            'description': 'Crowdsale opening time',
            'sorting_order': 80
        })
        make_title('closingTime', {
            'title': 'Closing time',
            'description': 'Crowdsale closing time',
            'sorting_order': 300
        })
        
        make_title("capReached", {
            'title': 'Hard cap reached',
            'description': 'Whether the hard cap was reached',
            'sorting_order': 90
        })
        make_title('goalReached', {
            'title': 'Soft cap reached',
            'sorting_order': 100            
        })        
        
        make_title('hasClosed', {
            'title': 'Has closed', 
            'description': 'Closing time has been reached',
            'sorting_order': 101      
        })

        make_title('isFinalized', {
            'title': 'Is finalized',
            'description': 'Finalize method has been called'
        })      
     
        make_title('mEscrow', {
            'title': 'Escrow contract',
            'description': 'Contract that return contribution if goal won\'t be reached',
            'sorting_order': 110
        })
      
        if fields.get('is_whitelisted', False):
            make_title('whitelist', {
                'title': 'Address in whitelist',
                'description': 'Determine if address is in whitelist',
                'inputs': [
                    {
                        'title': 'Address'
                    }
                ],
                'sorting_order': 301
            })
            make_title('checkRole',{
                'title': 'Check role',
                'description': 'Reverts if address does not have role',                
                'sorting_order': 301,
                'inputs': [
                    {
                        'title': 'Address',
                        'description': 'Checked address'
                    },
                    {
                        'title': 'Role',
                        'description': 'Role name. For example - whitelist'
                    }
                ]
            })
            make_title('addAddressToWhitelist', {
                'title': 'Add address to whitelist',
                'description': 'Only owner function.',
                'inputs': [
                        {
                            'title': 'Address',
                            'description': 'Whitelisted address'
                        },
                ],
                'sorting_order': 310,
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
                'sorting_order': 320,
                'icon': {
                        'pack': 'materialdesignicons',
                        'name': 'text'
                },
            })
            make_title('removeAddressFromWhitelist',{
                'title': 'Remove address from the whitelist',
                'description': '',
                'inputs': [
                    {
                        'title': 'Address'
                    }
                ],
                'sorting_order': 330,
            })
            make_title('removeAddressesFromWhitelist',{
                'title': 'Remove addresses from the whitelist',
                'description': '',
                'inputs': [
                    {
                        'title': 'Addresses'
                    }
                ],
                'sorting_order': 340,
            })
          

        
        
        make_title("buyTokens", {
            "title": 'Buy tokens',
            'description': 'Buy tokens for specific address',
            'inputs': [
                {
                    'title': 'Address',
                    'description': ''
                }
            ],
            'sorting_order': 2000})
              
        make_title('_rateChangeDates', {
            'title': 'Discount dates',
            'description': 'Dates thresholds for each discount price',
            'sorting_order': 1001
        })

        make_title('_tokenRates', {
            'title': 'Discount rates',
            'description': 'Token rate for each discount period',
            'sorting_order': 1002
        })

        make_title('finalize', {
            'title': 'Finalize',
            'description': 'Send funds on target address or return contributions if goal hasn\'t been reached. Can be called only once after ico has been closed',
            'sorting_order': 1000,

        })
        make_title('claimRefund', {
            'title': 'Refund',
            'description': 'Investors can claim refunds here if crowdsale is unsuccessful',
            'sorting_order': 1010,
        })
        make_title('renounceOwnership', {
            'title': 'Renounce ownership',
            'description': 'Allows the current owner to relinquish control of the contract.',
            'sorting_order': 1030,
        })
        make_title('transferOwnership', {
            'title': 'Transfer ownership',
            'description': 'Allows the current owner to transfer control of the contract to a new owner.',
            'inputs': [
                {
                    'title': 'New owner',
                    'description': 'The address to transfer ownership to.'
                }
            ],
             'sorting_order': 1040,
        })

        if fields.get('has_cap_per_person', False):
            make_title('caps', {
                'title': 'Per user caps',
                'description': '',
                'sorting_order': 200,

            })
            make_title('contributions', {
                'title': 'Per user contributions',
                'description': '',
                'sorting_order': 201,

            })

            make_title('getUserCap', {
                'title': 'User cap',
                'description': 'The cap of a specific user',               
                'sorting_order': 202,                
                'inputs': [
                    {
                        'title': 'Address'
                    }
                ]
            })

            make_title('setUserCap', {
                'title': 'Set user cap',
                'description': 'The cap of a specific user',                
                'sorting_order': 203,

                'inputs': [
                    {
                        'title': 'Address'
                    },
                    {
                        'title': 'Cap in wei'
                    }
                ]
            })
            make_title('setGroupCap', {
                'title': 'Set group cap',
                'description': 'The cap of a group of users',
                  'sorting_order': 204,
                'inputs': [
                    {
                        'title': 'Addresses'
                    },
                    {
                        'title': 'Cap in wei'
                    }
                ]

            })
            make_title('getUserContribution', {
                'title': 'User contribution',
                'description': 'The amount contributed so far by a sepecific user',
                'sorting_order': 205,
                'inputs': [
                    {
                        'title': 'Address'
                    }
                ]
            })
       
        return {
            "result": "success",
            'function_specs': function_titles,
            'dashboard_functions': ['weiRaised', 'goalReached']
        }


    # language=Solidity
    _TEMPLATE = """
{{ TEMPLATE }}
    """

    _PAYMENT_CODE="%payment_code%"
