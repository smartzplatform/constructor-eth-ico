from smartz.api.constructor_engine import ConstructorInstance
import re
import base64


def _if(var, default=""):
    if var == True or var != None:
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
                    "type": "bool",
                },
                "mintable_token": {
                    "title": "Is token mintable",
                    "description": "",
                    "type": "bool",
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
            
        fill_context('is_whitelisted', True)
        fill_context('cap', 1000000)
        fill_context('has_cap_per_person', True)
        fill_context('rate', 100)
        fill_context('wallet', '0x111111')
        fill_context('token', '0x222222')
        fill_context('softcap', 10000)
        fill_context('min_contribution', 1)
        fill_context('need_burn', True)
        fill_context('start', 10000)
        fill_context('end', 20000)
        template = base64.b64decode(self.__class__._TEMPLATE).decode('utf-8')
        return {
            "result": "success",
            'source': render_template(template, context),
            'contract_name': "ICO"
        }

    def post_construct(self, fields, abi_array):

        function_titles = {
             # View functions
            'Assertion': {
                'title': 'Assertion text',
                'description': 'Statement considered to be true by contract owner.',
                 'sorting_order': 10,
            },
            'Deadline': {
                'title': 'Deadline',
                'description': 'Current value of Deadline',
                "ui:widget": "unixTime",
                'sorting_order': 20,
            },
            'currentBet': {
                'title': 'Current bet amount',
                'description': 'Ether amount sent by contract owner to bet on assertion text is true',
                "ui:widget": "ethCount",
                'sorting_order': 30,
            },
            'OwnerAddress': {
                'title': 'Owner address',
                'description': 'Address of the bet contract owner. She deployed the contract, can change it\'s parameters before arbiter comes, and bet for assertion is true.',
                'sorting_order': 40,
            },
            'ArbiterAddress': {
                "title": "Arbiter address",
                "description": "Arbiter decides is the assertion true, false or can not be checked. She gets the fee for judging and stakes deposit as a guarantee of motivation to get job done. When arbiter agrees to judge, contract's terms become inviolable.",
                'sorting_order': 50,
            },
            'OpponentAddress': {
                "title": "Opponent address",
                "description": "Opponent bet for assertion is false. If this address set to 0x0000000000000000000000000000000000000000, anyone may become an opponent. Can bet only after arbiter agreed.",
                'sorting_order': 60,
            },
            'ArbiterFee': {
                'title': 'Arbiter fee percent',
                'description': 'Current value for arbiter fee as percent of bet amount',
                "ui:widget": "ethCount",
                'sorting_order': 70,
            },
            'ArbiterFeeAmountInEther': {
                'title': 'Arbiter fee in ether',
                'description': 'Calculated from bet amount and arbiter fee percent.',
                "ui:widget": "ethCount",
                'sorting_order': 80,
            },
            'ArbiterPenaltyAmount': {
                'title': 'Arbiter deposit amount',
                'description': 'Arbiter must freeze this amount as a incentive to judge this dispute.',
                "ui:widget": "ethCount",
                'sorting_order': 90,
            },
            'StateVersion': {
                "title": "State version number",
                "description": "Current state version number secures other participants from sudden changes in dispute terms by owner. Version changes every time owner edits the terms. Opponent and arbiter should specify which version do they mind when signing transactions to confirm their partaking in contract. If specified version not coincides with current, transaction reverts.",
                'sorting_order': 100,
            },
            'IsArbiterAddressConfirmed': {
                "title": "Arbiter agreed to judge",
                "description": "Arbiter has confirmed he is argee to judge this dispute with specific assertion text, deadline, bet, fee and penalty amount.",
                'sorting_order': 110,
            },
            'IsOpponentBetConfirmed': {
                "title": "Opponent confirmed his bet",
                "description": "Opponent made his bet opposite contract owner by transfering appropriate amount of ether to the smart contract.",
                'sorting_order': 120,
            },
            'ArbiterHasVoted': {
                "title": "Arbiter has made decision",
                "description": "Arbiter's decision can be one of: assertion is true, assertion is false, assertion can not be checked.",
                'sorting_order': 130,
            },
            'IsDecisionMade': {
                "title": "Arbiter considered assertion true or false",
                "description": "Arbiter confirmed that assertion is chacked and voted it is true or false.",
                'sorting_order': 140,
            },
            'IsAssertionTrue': {
                "title": "Assertion is true",
                "description": "Helper function for payouts calculations.",
                'sorting_order': 150,
            },
            'ownerPayout': {
                'title': 'Owner payout',
                'description': 'Amount of ether to be claimed by owner after dispute judged or failed.',
                "ui:widget": "ethCount",
                'sorting_order': 160,
            },
            'opponentPayout': {
                'title': 'Opponent payout',
                'description': 'Amount of ether to be claimed by opponent after dispute judged or failed.',
                "ui:widget": "ethCount",
                'sorting_order': 170,
            },
            'arbiterPayout': {
                'title': 'Arbiter payout',
                'description': 'Amount of ether to be claimed by arbiter after dispute judged or failed.',
                "ui:widget": "ethCount",
                'sorting_order': 180,
            },
            'IsOwnerTransferMade': {
                'title': 'Owner claimed payout',
                'description': 'Shows if an owner claimed his payout after dispute judged or failed.',
                'sorting_order': 190,
            },
            'IsOpponentTransferMade': {
                'title': 'Opponent claimed payout',
                'description': 'Shows if an owner claimed his payout after dispute judged or failed.',
                'sorting_order': 200,
            },
            'IsArbiterTransferMade': {
                'title': 'Arbiter claimed payout',
                'description': 'Shows if an owner claimed his payout after dispute judged or failed.',
                'sorting_order': 210,
            },
            'getTime': {
                'title': 'Current timestamp',
                'description': 'Just in case',
                "ui:widget": "unixTime",
                'sorting_order': 220,
            },
            # Write functions
            'setAssertionText': {
                'title': 'Change assertion text',
                'description': 'Only owner function. Can be called only before owner bet. Changes statement you bet to be true.',
                'inputs': [
                    {
                        'title': 'Assertion',
                        'description': 'Statement you bet to be true.'
                    },
                ],
                'sorting_order': 300,
                'icon': {
                    'pack': 'materialdesignicons',
                    'name': 'text'
                },
            },
            'setDeadline': {
                'title': 'Change deadline',
                'description': 'Only owner function. Can be called only before owner bet. Dispute should be resolved before this point in time, otherwise no one considered a winner. Choose a date and time in the future, otherwise transaction will fail.',
                'inputs': [
                    {
                        'title': 'new deadline',
                        'description': 'arbiter should be able to make decision before new deadline',
                        'ui:widget': 'unixTime'
                    },
                ],
                'sorting_order': 310,
                'icon': {
                    'pack': 'materialdesignicons',
                    'name': 'timer-sand'
                },
            },
            'setArbiterFee': {
                'title': 'Change arbiter fee percent',
                'description': 'Only owner function. Can be called only before arbiter agreed. Arbiter fee as % of bet amount, should be in range [0-100). For example, if you bet for 1 ether and feePercent is 10, arbiter will receive 0.1 ether, and the winner will receive 0.9 ether.',
                'inputs': [
                    {
                        'title': 'new fee percent [0,100.0)',
                        'description': 'change arbiter fee value before arbiter agreed to judge the dispute',
                        'ui:widget': 'ethCount'
                    },
                ],
                'sorting_order': 320,
                'icon': {
                    'pack': 'materialdesignicons',
                    'name': 'percent'
                },
            },
            'setArbiterPenaltyAmount': {
                'title': 'Change arbiter deposit',
                'description': 'Only owner function. Can be called only before arbiter agreed.',
                'inputs': [
                    {
                        'title': 'Deposit amount',
                        'description': 'Arbiter must freeze this amount as a incentive to judge this dispute.',
                        'ui:widget': 'ethCount'
                    },
                ],
                'sorting_order': 330,
                'icon': {
                    'pack': 'materialdesignicons',
                    'name': 'security-lock'
                },
            },
            'setArbiterAddress': {
                'title': 'Change arbiter address',
                'description': 'Only owner function. Can be called only before owner bet. Arbiter decides is the assertion true, false or can not be checked. She gets the fee for judging and stakes deposit as a guarantee of motivation to get job done. When arbiter agrees to judge, contract\'s terms become inviolable. Should be set before arbiter can agree, arbiter can not be random',
                'inputs': [
                    {
                        'title': 'Arbiter ethereum address',
                        'description': 'Arbiter ethereum address',
                    },
                ],
                'sorting_order': 340,
                'icon': {
                    'pack': 'materialdesignicons',
                    'name': 'security-account'
                },
            },
            'setOpponentAddress': {
                'title': 'Change opponnet address',
                'description': 'Only owner function. Can be called only before owner bet. Opponent bet for assertion is false.',
                'inputs': [
                    {
                        'title': 'Opponent address',
                        'description': 'Leave this field blank to let anyone become an opponent.',
                    },
                ],
                'sorting_order': 350,
                'icon': {
                    'pack': 'materialdesignicons',
                    'name': 'account-alert'
                },
            },
            'bet': {
                'title': 'Owner Bet',
                'description': 'Make owner bet',
                'payable_details': {
                    'title': 'Bet amount',
                    'description': 'Now you decide how much do you bet and accordingly how much your opponent should bet to take the challenge. Can not be changed.',
                },
                'sorting_order': 360,
                'icon': {
                    'pack': 'materialdesignicons',
                    'name': 'check-circle'
                },
            },
            'agreeToBecameArbiter': {
                'title': 'Agree to be an arbiter',
                'description': 'Only arbiter function. You agree to became an arbiter for this dispute and send penalty amount (if it is not set to zero by owner). When you agree, all contract\'s terms will freeze. You can self retreat before opponent bets.' ,
                'payable_details': {
                    'title': 'Arbiter deposit amount',
                    'description': 'Ether deposit amount (returned by "Arbiter deposit amount" function) to confim you are to freeze this ether as a guarantee you will judge the dispute. If you will not show, betters will split it.',
                },
                'inputs': [
                    {
                        'title': 'State version number',
                        'description': 'Returned by "State version number" function. This field secures you from sudden changes in dispute terms by owner. Version changes every time owner edits the terms. Opponent and arbiter should specify which version do they mind when signing transactions to confirm their partaking in contract. If specified version not coincides with current, transaction reverts.',
                    },
                ],
                'sorting_order': 370,
                'icon': {
                    'pack': 'materialdesignicons',
                    'name': 'check'
                },
            },
            'arbiterSelfRetreat': {
                'title': 'Arbiter self retreat',
                'description': 'Only arbiter function. After arbiter agreed but before opponent bet, arbiter may retreat and get her deposit back.',
                'sorting_order': 380,
                'icon': {
                    'pack': 'materialdesignicons',
                    'name': 'close'
                },
            },
            'betAssertIsFalse': {
                'title': 'Opponent Bet',
                'description': 'Make opponent bet for assertion text contains false statement',
                'payable_details': {
                    'title': 'Bet amount',
                    'description': 'Ether amount must be equal to owner bet as returned by "Current bet amount" (currentBet function)',
                },
                'inputs': [
                    {
                        'title': 'State version number',
                        'description': 'Returned by "State version number" function. This field secures you from sudden changes in dispute terms by owner. Version changes every time owner edits the terms. Opponent and arbiter should specify which version do they mind when signing transactions to confirm their partaking in contract. If specified version not coincides with current, transaction reverts.',
                    },
                ],
                'sorting_order': 390,
                'icon': {
                    'pack': 'materialdesignicons',
                    'name': 'alert-circle'
                },
            },
            'agreeAssertionTrue': {
                'title': 'Arbiter: assertion is True',
                'description': 'Only arbiter function. Arbiter confirm assertion text contains false statement (owner wins). After this function called, participants can claim their payouts.',
                'sorting_order': 400,
                'icon': {
                    'pack': 'materialdesignicons',
                    'name': 'comment-check-outline'
                },
            },
            'agreeAssertionFalse': {
                'title': 'Arbiter: assertion is False',
                'description': 'Only arbiter function. Arbiter confirm assertion text contains false statement (opponent wins). After this function called, participants can claim their payouts.',
                'sorting_order': 410,
                'icon': {
                    'pack': 'materialdesignicons',
                    'name': 'comment-remove-outline'
                },
            },
            'agreeAssertionUnresolvable': {
                'title': 'Arbiter: assertion can not be checked',
                'description': 'Only arbiter function. Arbiter affirms assertion can not be checked (everybody get their bets and deposits back). After this function called, participants can claim their payouts.',
                'sorting_order': 420,
                'icon': {
                    'pack': 'materialdesignicons',
                    'name': 'comment-question-outline'
                },
            },
            'withdraw': {
                'title': 'Get payout',
                'description': 'All participants of the contract claim their payouts with this function after dispute has ended.',
                'sorting_order': 430,
                'icon': {
                    'pack': 'materialdesignicons',
                    'name': 'currency-eth'
                },
            },
            'deleteContract': {
                'title': 'Drop contract',
                'description': 'Owner can drop the contract on some stages (for example, if there is no opponnet found).',
                'sorting_order': 440,
                'icon': {
                    'pack': 'materialdesignicons',
                    'name': 'delete'
                },
            },
        }

        return {
            "result": "success",
            'function_specs': function_titles,
            'dashboard_functions': ['Assertion', 'Deadline', 'currentBet', 'ArbiterHasVoted']
        }


    # language=Solidity
    _TEMPLATE = """
{{ TEMPLATE }}
    """