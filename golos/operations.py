# -*- coding: utf-8 -*-
"""
Contains the attribute :py:attr:`.type_op` which maps each transaction operation to a list of arguments and
their types.

Used by :py:meth:`golos.broadcast.Tx.get_digest` for generating a transaction digest.

"""
from .types import *

# Сериализатор
# https://github.com/GolosChain/golos-js/blob/master/src/auth/serializer/src/operations.js

type_op = {
    
    "vote":                           [['voter', String], ['author', String], ['permlink', String], ['weight', Int16]],
    
    "comment":                        [['parent_author', String], ['parent_permlink', String], ['author', String],
                                       ['permlink', String],
                                       ['title', String], ['body', String], ['json_metadata', String]],
    
    "transfer":                       [['from', String], ['to', String], ['amount', Amount], ['memo', String]],
    
    "transfer_to_vesting":            [['from', String], ['to', String], ['amount', Amount]],
    
    "withdraw_vesting":               [['account', String], ['vesting_shares', Amount]],
    
    "account_create":                 [['fee', Amount], ['creator', String], ['new_account_name', String],
                                       ['owner', Permission], ['active', Permission], ['posting', Permission],
                                       ['memo_key', PublicKey],
                                       ['json_metadata', String]],
    
    
    "account_update":                 [['account', String], ['owner', Optional_Permission],
                                       ['active', Optional_Permission],
                                       ['posting', Optional_Permission], ['memo_key', PublicKey],
                                       ['json_metadata', String]],
    
    
    "custom_json":                    [['required_auths', ArrayString], ['required_posting_auths', ArrayString],
                                       ['id', String], ['json', String]],
    
    
    "comment_options":                [['author', String], ['permlink', String], ['max_accepted_payout', Amount],
                                       ['percent_steem_dollars', Uint16], ['allow_votes', Bool],
                                       ['allow_curation_rewards', Bool],
                                       ['extensions', ExtensionsComment]],
    
    "change_recovery_account":        [['account_to_recover', String], ['new_recovery_account', String],
                                       ['extensions', Set]],
    
    "delegate_vesting_shares":        [['delegator', String], ['delegatee', String], ['vesting_shares', Amount]],
    
    "account_create_with_delegation": [['fee', Amount], ['delegation', Amount], ['creator', String],
                                       ['new_account_name', String],
                                       ['owner', Permission], ['active', Permission], ['posting', Permission],
                                       ['memo_key', PublicKey],
                                       ['json_metadata', String], ['extensions', Set]],
    
    "account_metadata":               [['account', String], ['json_metadata', String]],
    
    "delegate_vesting_shares_with_interest":
                                      [['delegator', String], ['delegatee', String], ['vesting_shares', Amount],
                                       ['interest_rate', Uint16], ['extensions', Set]],
    
}
"""
A dictionary which maps each GOLOS operation such as ``vote`` - to a list of argument pairs (``['arg_name', String]``)
which map each argument of the operation to it's type in :py:mod:`.types` 

Example:

	>>> type_op['vote']
	[
		['voter', <class 'golos.types.String'>], ['author', <class 'golos.types.String'>], 
		['permlink', <class 'golos.types.String'>], ['weight', <class 'golos.types.Int16'>]
	]

"""

# "withdraw_vesting":				[['account', String], ['vesting_shares', Amount]],
# "set_withdraw_vesting_route":	[['from_account', String], ['to_account', String], ['percent', Uint16], ['auto_vest', Bool]],
#
# "account_witness_proxy":		[['account', String], ['proxy', String]],
# "account_witness_vote":			[['account', String], ['witness', String], ['approve', Bool]],
# "account_update":				[['account', String], ['master', Optional_Permission], ['active', Optional_Permission],
# 								['regular', Optional_Permission], ['memo_key', PublicKey], ['json_metadata', String]],
#
# "custom":	 					[['required_active_auths', ArrayString], ['required_regular_auths', ArrayString],
# 								['id', String], ['json', String]],
