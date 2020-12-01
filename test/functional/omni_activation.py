#!/usr/bin/env python3
# Copyright (c) 2015-2017 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test basic for Features activation """

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import *

import os
import json
import http.client
import urllib.parse

class ActivationBasicsTest (BitcoinTestFramework):
    def __init__(self):
        super().__init__()
        self.num_nodes = 1
        self.setup_clean_chain = True
        self.extra_args = [["-txindex=1", "-datacarriersize=220", "-omniactivationallowsender=moSfCMqU8rjB99n7Rm5pBgRvRGevyKVJzY"]]

    def setup_network(self):
        self.setup_nodes()

    def run_test(self):

        self.log.info("Preparing the workspace...")

        # mining 200 blocks
        self.nodes[0].generate(200)

        ################################################################################
        # checking omni_senddeactivation and omni_senddeactivation                     #
        ################################################################################

        url = urllib.parse.urlparse(self.nodes[0].url)

        #Old authpair
        authpair = url.username + ':' + url.password

        headers = {"Authorization": "Basic " + str_to_b64str(authpair)}

        addresses = []
        accounts = ["john", "doe", "another"]

        conn = http.client.HTTPConnection(url.hostname, url.port)
        conn.connect()

        adminAddress = 'moSfCMqU8rjB99n7Rm5pBgRvRGevyKVJzY'
        privkey = 'cQxt12eUkTiMUSfVQP7FisbAQJk4vmCotmHxraz3efyatEWiwyLp'

        self.log.info("importing admin address")
        params = str([privkey]).replace("'",'"')
        out = omnilayer_HTTP(conn, headers, True, "importprivkey",params)
        # self.log.info(out)
        assert_equal(out['error'], None)

        self.log.info("Creating sender address")
        addresses = omnilayer_createAddresses(accounts, conn, headers)
        addresses.append(adminAddress)

        self.log.info("Funding addresses with BTG")
        amount = 0.1
        omnilayer_fundingAddresses(addresses, amount, conn, headers)

        self.log.info("Checking the BTG balance in every account")
        omnilayer_checkingBalance(accounts, amount, conn, headers)


        # deactivation here to write 999999999 in the MSC_SP_BLOCK param
        params = str([adminAddress, 1]).replace("'",'"')
        out = omnilayer_HTTP(conn, headers, False, "omni_senddeactivation",params)
        # self.log.info(out)

        self.nodes[0].generate(1)

        self.log.info("Creating new tokens (must be rejected)")
        params = str([addresses[0], 1, 2, 0,"N/A", "N/A", "lihki", "url", "data", "3000"]).replace("'",'"')
        out = omnilayer_HTTP(conn, headers, True, "omni_sendissuancefixed",params)
        # self.log.info(out)

        self.nodes[0].generate(1)

        self.log.info("Checking the property (doesn't exist)")
        params = str([3])
        out = omnilayer_HTTP(conn, headers, False, "omni_getproperty",params)
        # self.log.info(out)
        assert_equal(out['error']['message'], 'Property identifier does not exist')

        self.log.info("Testing omni_sendactivation")

        # adminAddress, activation number 1, in block 400, min omni version = 1.
        params = str([adminAddress, 1, 400, 1]).replace("'",'"')
        out = omnilayer_HTTP(conn, headers, False, "omni_sendactivation",params)
        # self.log.info(out)

        self.nodes[0].generate(210)

        self.log.info("Creating new tokens")
        params = str([addresses[0], 1, 2, 0,"N/A", "N/A", "lihki", "url", "data", "3000"]).replace("'",'"')
        out = omnilayer_HTTP(conn, headers, True, "omni_sendissuancefixed",params)
        # self.log.info(out)

        self.nodes[0].generate(1)

        self.log.info("Checking the property")
        params = str([3])
        out = omnilayer_HTTP(conn, headers, False, "omni_getproperty",params)
        # self.log.info(out)
        assert_equal(out['result']['propertyid'],3)
        assert_equal(out['result']['name'],'lihki')
        assert_equal(out['result']['issuer'], addresses[0])
        assert_equal(out['result']['data'],'data')
        assert_equal(out['result']['url'],'url')
        assert_equal(out['result']['divisible'],True)
        assert_equal(out['result']['totaltokens'],'3000.00000000')

        self.log.info("Testing omni_senddeactivation")

        # adminAddress, deactivation number 1, min omni version = 1.
        params = str([adminAddress, 1]).replace("'",'"')
        out = omnilayer_HTTP(conn, headers, False, "omni_senddeactivation",params)
        # self.log.info(out)

        self.nodes[0].generate(1)

        self.log.info("Creating new tokens (must be rejected)")
        params = str([addresses[0], 1, 2, 0,"N/A", "N/A", "lihki", "url", "data", "3000"]).replace("'",'"')
        out = omnilayer_HTTP(conn, headers, True, "omni_sendissuancefixed",params)
        # self.log.info(out)

        self.nodes[0].generate(1)

        self.log.info("Checking the property (doesn't exist)")
        params = str([4])
        out = omnilayer_HTTP(conn, headers, False, "omni_getproperty",params)
        # self.log.info(out)
        assert_equal(out['error']['message'], 'Property identifier does not exist')

        conn.close()


if __name__ == '__main__':
    ActivationBasicsTest ().main ()
