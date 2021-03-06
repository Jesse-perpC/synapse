# -*- coding: utf-8 -*-
# Copyright 2014-2016 OpenMarket Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from unpaddedbase64 import encode_base64

from synapse.storage._base import SQLBaseStore
from synapse.util.caches.descriptors import cached, cachedList


class SignatureWorkerStore(SQLBaseStore):
    @cached()
    def get_event_reference_hash(self, event_id):
        # This is a dummy function to allow get_event_reference_hashes
        # to use its cache
        raise NotImplementedError()

    @cachedList(
        cached_method_name="get_event_reference_hash", list_name="event_ids", num_args=1
    )
    def get_event_reference_hashes(self, event_ids):
        def f(txn):
            return {
                event_id: self._get_event_reference_hashes_txn(txn, event_id)
                for event_id in event_ids
            }

        return self.db_pool.runInteraction("get_event_reference_hashes", f)

    async def add_event_hashes(self, event_ids):
        hashes = await self.get_event_reference_hashes(event_ids)
        hashes = {
            e_id: {k: encode_base64(v) for k, v in h.items() if k == "sha256"}
            for e_id, h in hashes.items()
        }

        return list(hashes.items())

    def _get_event_reference_hashes_txn(self, txn, event_id):
        """Get all the hashes for a given PDU.
        Args:
            txn (cursor):
            event_id (str): Id for the Event.
        Returns:
            A dict[unicode, bytes] of algorithm -> hash.
        """
        query = (
            "SELECT algorithm, hash"
            " FROM event_reference_hashes"
            " WHERE event_id = ?"
        )
        txn.execute(query, (event_id,))
        return {k: v for k, v in txn}


class SignatureStore(SignatureWorkerStore):
    """Persistence for event signatures and hashes"""
