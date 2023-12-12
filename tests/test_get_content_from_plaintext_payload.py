import email
from email.policy import default as default_policy
import pytest
from tlmail.__main__ import extract_body_from_email_message

payload = """\
Received: from AS8PR09MB4758.eurprd09.prod.outlook.com (2603:10a6:20b:29e::22)
 by DB6PR0902MB2040.eurprd09.prod.outlook.com with HTTPS; Tue, 19 Jul 2022
 07:41:10 +0000
Received: from SV0P279CA0009.NORP279.PROD.OUTLOOK.COM (2603:10a6:f10:11::14)
 by AS8PR09MB4758.eurprd09.prod.outlook.com (2603:10a6:20b:29e::22) with
 Microsoft SMTP Server (version=TLS1_2,
 cipher=TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384) id 15.20.5417.20; Tue, 19 Jul
 2022 07:41:09 +0000
Received: from HE1EUR04FT033.eop-eur04.prod.protection.outlook.com
 (2603:10a6:f10:11:cafe::52) by SV0P279CA0009.outlook.office365.com
 (2603:10a6:f10:11::14) with Microsoft SMTP Server (version=TLS1_2,
 cipher=TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384) id 15.20.5438.14 via Frontend
 Transport; Tue, 19 Jul 2022 07:41:09 +0000
Authentication-Results: spf=pass (sender IP is 10.10.19.169)
 smtp.mailfrom=externos.unared.es; dkim=pass (signature was verified)
 header.d=unared.es;dmarc=pass action=none
 header.from=unared.es;compauth=pass reason=100
Received-SPF: Pass (protection.outlook.com: domain of externos.unared.es
 designates 10.10.19.169 as permitted sender)
 receiver=protection.outlook.com; client-ip=10.10.19.169;
 helo=mx02.puc.unared.es; pr=C
Received: from mx02.puc.unared.es (10.10.19.169) by
 HE1EUR04FT033.mail.protection.outlook.com (10.152.27.36) with Microsoft SMTP
 Server (version=TLS1_2, cipher=TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384) id
 15.20.5438.12 via Frontend Transport; Tue, 19 Jul 2022 07:41:08 +0000
X-IncomingTopHeaderMarker:
 OriginalChecksum:72086C00E1005CF1E9C6D4058ECB3DC1A4D0720E3B7D6727D8AEFB3619A8858A;UpperCasedChecksum:9F102146D3EC0DBD249EFADF93A4BEC5557B5A75284C8F88C3C6AC89FD5B9A37;SizeAsReceived:4702;Count:38
Received: from mta-out02.sim.unared.es (mta-out02.sim.unared.es [10.10.24.44])
	by mx02.puc.unared.es  with ESMTP id 26J7f85q019879-26J7f85s019879
	(version=TLSv1.3 cipher=TLS_AES_256_GCM_SHA384 bits=256 verify=NO)
	for <javier.artiga@outlook.com>; Tue, 19 Jul 2022 09:41:08 +0200
Received: from mta-out02.sim.unared.es (localhost.localdomain [127.0.0.1])
	by mta-out02.sim.unared.es (Postfix) with ESMTPS id E7D88C0F386
	for <javier.artiga@outlook.com>; Tue, 19 Jul 2022 09:41:07 +0200 (CEST)
Received: from localhost (localhost.localdomain [127.0.0.1])
	by mta-out02.sim.unared.es (Postfix) with ESMTP id B207BC18E49
	for <javier.artiga@outlook.com>; Tue, 19 Jul 2022 09:41:07 +0200 (CEST)
DKIM-Filter: OpenDKIM Filter v2.10.3 mta-out02.sim.unared.es B207BC18E49
DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed; d=unared.es;
	s=469D46C0-5070-11E9-83F8-8CA6B83CDAF6; t=1658216467;
	bh=qyxpUbalQDkudwEQFMAqq2DIciBWu24Y6zGkqcZf3/A=;
	h=From:Message-ID:Date:MIME-Version;
	b=kRH1hRMzxfkp/XEa6OrNs9jnZxJ1yFxSv/2YlPf1mNZAa+Y2oAB2Bzcfu+lhYEO4M
	 /8iUBffw2qi/wsjTTfMFxf47lnb39vcdXi1zIk8PM2TbyAr+ia+tA54Mr8a4Fg0nCj
	 9hdRAnPY7RzJlfdHM2qq/IAQEIMDOooOh5Rb6g5jgGe/6LgIqrvU0lSDNJ3fuTLSsU
	 4uwiQktTGSdDsYBfWfbRVNvdRyJnYtpHRXrNFQc1uhm5vg8siLuuHL2tPtcUwoMx8Z
	 MegAOh2x5O1mrPrHvrluImzJ2YkS4fhylszu1Zy2+pXayT8qTfS2KoQhacSKKKHhU+
	 V9DeDYM6FHoyg==
X-Amavis-Modified: Mail body modified (using disclaimer) -
	mta-out02.sim.unared.es
Received: from mta-out02.sim.unared.es ([127.0.0.1])
	by localhost (mta-out02.sim.unared.es [127.0.0.1]) (amavisd-new, port 10026)
	with ESMTP id muHVRLKyqWMr for <javier.artiga@outlook.com>;
	Tue, 19 Jul 2022 09:41:07 +0200 (CEST)
Received: from store_unared_01.sim.unared.es (store_unared_01.sim.unared.es [10.10.24.77])
	by mta-out02.sim.unared.es (Postfix) with ESMTP id 5288DC0F386
	for <javier.artiga@outlook.com>; Tue, 19 Jul 2022 09:41:07 +0200 (CEST)
Received: from satellite01.sim.unared.es (LHLO satellite01.sim.unared.es)
 (10.10.24.60) by store_unared_01.sim.unared.es with LMTP; Tue, 19 Jul
 2022 09:41:06 +0200 (CEST)
Received: from satellite01.sim.unared.es (localhost.localdomain [127.0.0.1])
	by satellite01.sim.unared.es (Postfix) with ESMTPS id 60A1080A1D1;
	Tue, 19 Jul 2022 09:41:06 +0200 (CEST)
Received: from localhost (localhost.localdomain [127.0.0.1])
	by satellite01.sim.unared.es (Postfix) with ESMTP id 42EFE86D564;
	Tue, 19 Jul 2022 09:41:06 +0200 (CEST)
DKIM-Filter: OpenDKIM Filter v2.10.3 satellite01.sim.unared.es 42EFE86D564
DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed; d=unared.es;
	s=469D46C0-5070-11E9-83F8-8CA6B83CDAF6; t=1658216466;
	bh=qyxpUbalQDkudwEQFMAqq2DIciBWu24Y6zGkqcZf3/A=;
	h=From:Message-ID:Date:MIME-Version;
	b=EE9xLu1zkvcRcVxPXlbD8AXPoU8Wyr2IdIxX6gm3v1UIo9PMJfV8FP4KaH+BhklCg
	 3+nNp/yrbbHuLi/Owvvd1vALpNoJbAXeniJ+2p5yKT0YhzlPYjX1UZFgZx5RfOSi+k
	 t18DTOEoQK4JUcI5lmaLr4OWSHGwW00hKCLHJIzdXi4G7nWrBdBXwES7j6lzYgzCfv
	 a6Od/q0aeDT+WgHSv0JRpmjloyVxNK7RMRePDZLhEvZbESHSy6aXSQKjzOsOm8Jp0w
	 GJbciZCYrPo/YY88T3fgv8D005vWxsdaUlB3kROi0F7Uhz6BiXEvgfFmag7+x8lV+h
	 TAqgIAXgLTBYw==
X-Amavis-Modified: Mail body modified (using disclaimer) -
	satellite01.sim.unared.es
Received: from satellite01.sim.unared.es ([127.0.0.1])
	by localhost (satellite01.sim.unared.es [127.0.0.1]) (amavisd-new, port 10026)
	with ESMTP id vIJEPj4SAAst; Tue, 19 Jul 2022 09:41:06 +0200 (CEST)
Received: from support.unared.es (support.unared.es [10.10.3.52])
	by satellite01.sim.unared.es (Postfix) with ESMTP id DD99D85D5E1;
	Tue, 19 Jul 2022 09:41:05 +0200 (CEST)
Received: by support.unared.es (Postfix, from userid 48)
	id CDBE71BE53C; Tue, 19 Jul 2022 09:41:05 +0200 (CEST)
X-RT-Queue: DNSFirewall
X-RT-Owner: Nobody
X-RT-Status: new
Subject: [DNS-FW #894024] Alta en servicio
From: "CLIENTE1 via RT" <dnsfirewall@unared.es>
Reply-To: dnsfirewall@unared.es
In-Reply-To: <DU0PR07MB84925132462ADB8261E3ECB4EC8F9@DU0PR07MB8492.eurprd07.prod.outlook.com>
References: <RT-Ticket-894024@unared.es>
 <DU0PR07MB84925132462ADB8261E3ECB4EC8F9@DU0PR07MB8492.eurprd07.prod.outlook.com>
Message-ID: <rt-4.2.12-49817-1658216465-938.894024-190-0@unared.es>
X-RT-Loop-Prevention: unared.es
X-RT-Ticket: unared.es #894024
X-Managed-BY: RT 4.2.12 (http://www.bestpractical.com/rt/)
X-RT-Originator: cliente1@ceu.es
Content-Type: text/plain; charset="utf-8"
X-RT-Original-Encoding: utf-8
Precedence: bulk
Date: Tue, 19 Jul 2022 09:41:05 +0200
Content-Transfer-Encoding: quoted-printable
X-Zimbra-Forwarded: tecni1@externos.unared.es
X-FE-Policy-ID: 23:8:4:SYSTEM
X-IncomingHeaderCount: 38
To: Undisclosed recipients:;
Return-Path: tecni1@externos.unared.es
X-MS-Exchange-Organization-ExpirationStartTime: 19 Jul 2022 07:41:09.0193
 (UTC)
X-MS-Exchange-Organization-ExpirationStartTimeReason: OriginalSubmit
X-MS-Exchange-Organization-ExpirationInterval: 1:00:00:00.0000000
X-MS-Exchange-Organization-ExpirationIntervalReason: OriginalSubmit
X-MS-Exchange-Organization-Network-Message-Id:
 4d98588d-c130-4777-cc28-08da695a0bac
X-EOPAttributedMessage: 0
X-EOPTenantAttributedMessage: 84df9e7f-e9f6-40af-b435-aaaaaaaaaaaa:0
X-MS-Exchange-Organization-MessageDirectionality: Incoming
X-MS-PublicTrafficType: Email
X-MS-Exchange-Organization-AuthSource:
 HE1EUR04FT033.eop-eur04.prod.protection.outlook.com
X-MS-Exchange-Organization-AuthAs: Anonymous
X-MS-UserLastLogonTime: 7/19/2022 6:55:27 AM
X-MS-Office365-Filtering-Correlation-Id: 4d98588d-c130-4777-cc28-08da695a0bac
X-MS-TrafficTypeDiagnostic: AS8PR09MB4758:EE_
X-MS-Exchange-EOPDirect: true
X-Sender-IP: 10.10.19.169
X-SID-PRA: DNSFIREWALL@unared.ES
X-SID-Result: PASS
X-MS-Exchange-Organization-PCL: 2
X-MS-Exchange-Organization-SCL: 1
X-Microsoft-Antispam: BCL:0;
X-MS-Exchange-CrossTenant-OriginalArrivalTime: 19 Jul 2022 07:41:08.8162
 (UTC)
X-MS-Exchange-CrossTenant-Network-Message-Id: 4d98588d-c130-4777-cc28-08da695a0bac
X-MS-Exchange-CrossTenant-Id: 84df9e7f-e9f6-40af-b435-aaaaaaaaaaaa
X-MS-Exchange-CrossTenant-AuthSource:
 HE1EUR04FT033.eop-eur04.prod.protection.outlook.com
X-MS-Exchange-CrossTenant-AuthAs: Anonymous
X-MS-Exchange-CrossTenant-FromEntityHeader: Internet
X-MS-Exchange-CrossTenant-RMS-PersistedConsumerOrg:
 00000000-0000-0000-0000-000000000000
X-MS-Exchange-Transport-CrossTenantHeadersStamped: AS8PR09MB4758
X-MS-Exchange-Transport-EndToEndLatency: 00:00:01.4407996
X-MS-Exchange-Processed-By-BccFoldering: 15.20.5438.023
X-Microsoft-Antispam-Mailbox-Delivery:
	abwl:0;wl:0;pcwl:0;kl:0;iwl:0;ijl:0;dwl:0;dkl:0;rwl:0;ucf:0;jmr:0;ex:0;auth:1;dest:I;ENG:(5062000285)(90000117)(90010023)(91010020)(91040095)(5061607266)(5061608174)(9050020)(9100338)(2008001134)(4810004)(4910013)(9575002)(10195002)(9320005);
X-Message-Info:
	5vMbyqxGkdf1zx3xYbUI7KyrjaUHETL3HQaCmxD/DbvDHDsUDzNrWyRMhano/hpyz+Sj7tHInxocTzFdbvC8OVfWMGOF1eifOth6Wm5U0yi7d5YW2ayYxrnZma5tbaHy+lj7f9majNc4AlGu9bckYKLv/aPjDjWr5Vj3C4aEHUezqhmms8vmMRSpblK9aCQ/3DkY5BFpDMjGX2kyfGnffg==
X-Message-Delivery: Vj0xLjE7dXM9MDtsPTA7YT0xO0Q9MTtHRD0xO1NDTD0z
X-Microsoft-Antispam-Message-Info:
	=?utf-8?B?VUZhMVZuV0dvYTRBQWMvZW9qZGpEQXRhOGtZSS84RkxRSU9UT0JKRXNmWmxk?=
 =?utf-8?B?UXVLL0Z1c1JYSmVNWC9heDJPOWREMGc5SXlnVVNBYUVhbUJIQyt0T1BDeFdp?=
 =?utf-8?B?SmtNdmZjWmhNc0s3YVFUc1VHUncySzkra3dDTzl3ZWlFdllML2xRVTZwSGJT?=
 =?utf-8?B?VVRwT3pqZHFnTzdnK25Tb2kwY1dLaVlnUVpUcjVpalRGajJSaWw3cGJKWlVi?=
 =?utf-8?B?Vm1wZmd1MjAvNEZtV2h1Z3RmZ2hSdFRKN2dtOEZ2V0FLSFFSWEpTbVE5cHND?=
 =?utf-8?B?QjM3OGpnOGJkK0cySXI1eXdkVGFKRlplS294ckdYMkk1V0Y0UC9SbURETDJ0?=
 =?utf-8?B?U0E2WlE5c01TdGlvNXZHdlZtUXFLQVJ0REVGVHVGeVV6N0F2ZHg4RTJNNEJl?=
 =?utf-8?B?eTl4Q3ZaWC9CM0hRRnZVaEdSaU56TDFHWWtpa2Z1T0ZiSzYrd3BCOGcwbXV5?=
 =?utf-8?B?cEZMOVhlSzFSaEJhdkJKank1Qjg0dXlpUEtlWVJjVm1wYlZKNGlKQm9DSGNR?=
 =?utf-8?B?T3MrRnoxNzBydWpFeHUzUitEellkV1lDUHlzdUI5SWJaYnl0TUlXQS9KV3kv?=
 =?utf-8?B?RlNIanVMKzBOcTA5SXRYUjV0TTU5Z2xyclFwN09VZk9kbEs1LzhxMTVGaFVU?=
 =?utf-8?B?SFNMYkhnYVVRUFRQUGdENU9EMDVVTkhxSTVrVy8ybGJTbnlnMFpsLzNhWWV4?=
 =?utf-8?B?QlJ5a1I2Y0hxaDh1RGxFS1pFazJHaFoyWk1hTG8wTFd0ZE5Pa09uQXl6LzRF?=
 =?utf-8?B?aFFBYTVWM2JaaEs4NUV2NnZ5cUdZSWdNNWVDaTh3dzFnamwzTi9RTFlJUGdU?=
 =?utf-8?B?aGhKVGkwdHE1WVhtMGhpQ0NnQXZoWjY5YUw5TktzamgwNkMrbk9pV2gzWTU0?=
 =?utf-8?B?SUF4NXUyTTNSUTFXVXZrbmFLTWJJeXl0T2tEa3Mxay85ajNCMWdSRS9HSUdo?=
 =?utf-8?B?UGlQbEUwTHRJY05ubGN5UHYvQTA1b1BTeTFZSTk1cnJGWXdkcFJFY2o4K2xx?=
 =?utf-8?B?Um8rTkRhbVhhZVF4c3Z3S3dpTWRwZlpscGdDL25hL3V5MUsrM2NiSDFQWUhr?=
 =?utf-8?B?NzRSOGxtS2NqakMvQWZxamdLeWJXNE5WbWJWSzZSYW9lS0xFVzZmSkN0NG1R?=
 =?utf-8?B?aS9OOXh4NFg1YjRxejNTenN3TWF3VUlqQ3VXRVRoTDk3MlloK3dsOHFnKzkr?=
 =?utf-8?B?c0J5TG9UbVZoOURpSFk2VVVJU0JLWHJPMWI0dDhTNXFid3VpaEJ2Y2RYV3FS?=
 =?utf-8?B?cFgzR1lzYW1SeDZ3d3NGSjNteWFvcW0reU4zK1VyUS9CWFR3K0tGQkIwYWpZ?=
 =?utf-8?B?SUgvS0luTDNxazJaaVlpT3liamd0ZE1SNGkzQXVDemoyQXVVQ1pvMVlnc0dh?=
 =?utf-8?B?NkRZeXpZZDZuKytlNnJIanY2VDZsamR5emVQYXFPN3FRY3ppK2Jzam93dXov?=
 =?utf-8?B?VzNaQ1B0ZmpNbDZGMU8xUkNUOWdkQUNrNEpic3BtdFVKcWhJRkp4MldoVzlM?=
 =?utf-8?B?bU5SZDRiT3VrMGwrNFVrZUs4K1ZoMHB4akpvM0tINE51Wk9QcURlTy93eldR?=
 =?utf-8?B?MHhaczd3WTk5em9JTDlwVmQxS3JRM2hwaUQyTmJhdUNOS3VNMFdXYVBoa3Vq?=
 =?utf-8?B?UWs1VEc1bmp1Z2dyTEhqY0dkbEM4Q3J3eTdCZDNhOGk5K0JVbU1sL1p3Q25w?=
 =?utf-8?B?bnR1b3ovUXFrbHFiSjRBS2I3cm9CQnkwRU5sT0dBaGhDOUZ5ZXJDbXVVZWtu?=
 =?utf-8?B?M3NZKzJTcWtzVHE2eDIvbk1pa05PNHI0RGd1aVlKOG5TeGVLa2R2OHBmVXg5?=
 =?utf-8?B?dHlHdVJ5RnA1M3JGMGlzbEkyWHZNT0ZzU3pPUlJNNmNaOUpSU00yKzBOdzBl?=
 =?utf-8?B?SkxtMDJxckRWa0ptdEZqZlBZSmxTcHkyb2h2WS9aT096MmtiNmJCc0tUUjFN?=
 =?utf-8?Q?vN9HwG3AVaqLznaCX++VYyV0qpXA8ET6?=
MIME-Version: 1.0

Se ha enviado una respuesta al ticket:

URL: <https://support.unared.es/Ticket/Display.html?id=1 >\
"""

def test_get_content_from_plaintext_payload():
    msg = email.message_from_string(payload, policy=default_policy)

    assert extract_body_from_email_message(msg, remove_html_tags=False) == """\
Se ha enviado una respuesta al ticket:

URL: <https://support.unared.es/Ticket/Display.html?id=1 >\
"""
