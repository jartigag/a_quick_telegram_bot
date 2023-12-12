import email
from email.policy import default as default_policy
import pytest
from tlmail.__main__ import extract_body_from_email_message

payload = """\
Received: from AM6PR0202MB3318.eurprd02.prod.outlook.com
 (2603:10a6:209:1c::11) by HE1PR0201MB2121.eurprd02.prod.outlook.com with
 HTTPS; Wed, 17 Nov 2021 10:25:47 +0000
ARC-Seal: i=2; a=rsa-sha256; s=arcselector9901; d=microsoft.com; cv=pass;
 b=B6jOj38WlG5FVBsG2a4iUvKRibwF1+SzZp7KD0p1UjanW//FiuuF8DgrzLRfgpUhh6uPxrNlxTKV+mh5AGUpAIHaUqASliQ37DIWnxqSs7bf232LJTb+ipWEqowjt4JoIFBYA1SVVvvAOyMSyN7msYx9GGSPgtIlkPKCprPp54PccGdxOuAktbabk4uYte7sDtN8+nIjbIVsCP0G2rKPRolxkCG/Ir6HLI+YPKQyl+QRiMYZPrUa3w/CDbrR2yMVfJUxg0fFxsyQieEyiFWBBaQC7REf6jBahmX9obluXjxXofSUo5TY++80xf/BW+MCoSRk63CNTTfZrTmJTefpLQ==
ARC-Message-Signature: i=2; a=rsa-sha256; c=relaxed/relaxed; d=microsoft.com;
 s=arcselector9901;
 h=From:Date:Subject:Message-ID:Content-Type:MIME-Version:X-MS-Exchange-AntiSpam-MessageData-ChunkCount:X-MS-Exchange-AntiSpam-MessageData-0:X-MS-Exchange-AntiSpam-MessageData-1;
 bh=8GOHbrHGAse+VwxwQ8bctFOzUmEf/xdtJgHt1uVZBJc=;
 b=kCMZyGaGlMJBUicHv1pVlFKPb/KzV+YT7FJRzLqQXD/amnyC522UyXzepija2JHrMbwuNi2Zvi45Qy2BO0+/9lu2Mg3TLZMR9eW+1ms+B3scbGxIKiNktu1kVjVdFf39nV2cq10JCTMr9agsqlJ2ivLHWpGBlF2wgBaKyl9VU+BFhByq5lgvfbcohwRaHIaw8HEJePsviHIh/alFdFGy9z6tXEFd2fCx1N7prG0doHwsNjJqdSQANrBoExk1FaBB9nGOqFpXeBZqSu+NDYv1VAsLb3sEcTB+KJzr7bZfN8glyCLCuP927Lv3eoH+mnk+0e1QUcreFp8TVbc0qIDuug==
ARC-Authentication-Results: i=2; mx.microsoft.com 1; spf=pass (sender ip is
 40.107.94.50) smtp.rcpttodomain=outlook.com
 smtp.mailfrom=accountprotection.microsoft.com; dmarc=pass (p=reject sp=reject
 pct=100) action=none header.from=accountprotection.microsoft.com; dkim=pass
 (signature was verified) header.d=accountprotection.microsoft.com; arc=pass
 (0 oda=0 ltdi=1)
Received: from DM3PR12CA0058.namprd12.prod.outlook.com (2603:10b6:0:56::26) by
 AM6PR0202MB3318.eurprd02.prod.outlook.com (2603:10a6:209:1c::11) with
 Microsoft SMTP Server (version=TLS1_2,
 cipher=TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384) id 15.20.4669.15; Wed, 17 Nov
 2021 10:25:46 +0000
Received: from DM6NAM12FT021.eop-nam12.prod.protection.outlook.com
 (2603:10b6:0:56:cafe::b6) by DM3PR12CA0058.outlook.office365.com
 (2603:10b6:0:56::26) with Microsoft SMTP Server (version=TLS1_2,
 cipher=TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384) id 15.20.4713.19 via Frontend
 Transport; Wed, 17 Nov 2021 10:25:45 +0000
Authentication-Results: spf=pass (sender IP is 40.107.94.50)
 smtp.mailfrom=accountprotection.microsoft.com; dkim=pass (signature was
 verified) header.d=accountprotection.microsoft.com;dmarc=pass action=none
 header.from=accountprotection.microsoft.com;compauth=pass reason=100
Received-SPF: Pass (protection.outlook.com: domain of
 accountprotection.microsoft.com designates 40.107.94.50 as permitted sender)
 receiver=protection.outlook.com; client-ip=40.107.94.50;
 helo=NAM10-MW2-obe.outbound.protection.outlook.com;
Received: from NAM10-MW2-obe.outbound.protection.outlook.com (40.107.94.50) by
 DM6NAM12FT021.mail.protection.outlook.com (10.13.179.220) with Microsoft SMTP
 Server (version=TLS1_2, cipher=TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384) id
 15.20.4713.9 via Frontend Transport; Wed, 17 Nov 2021 10:25:45 +0000
X-IncomingTopHeaderMarker:
 OriginalChecksum:6AB610A8F308BC9A10BB189351596AC832B2F565F4D46576766C7FE88F756F28;UpperCasedChecksum:4BE0F9933062307343C93DD9996FAD8F53B34411563067A6FCF4C0DFA4786747;SizeAsReceived:6114;Count:40
ARC-Seal: i=1; a=rsa-sha256; s=arcselector9901; d=microsoft.com; cv=none;
 b=DS6Gocb+GhHgikS7d3Y51kDrJ9Z+BpZ6tjsAK4TJjM71lpYUnA+WUF0tj4ob42EDpdlVOO/0NkJ9Od3rAwwV1jIiSPBeggzP417ofgxzEI2Q49q8T4cRvdmyVeYCxoVCUn+OZvhckLGBJuTQOdu7h7i4K0EZitU/8wS7fk/lifh4KFFWAAR1sXlsJm/egnCyK4Xp84cKFM/KTbVrVHP1tgiYd5Qm2u9tgyR6uimsQwBVhBquI0njZj5eOVbFEZtlMn5bLV04w8252EASaTC6uaAYYM7irCvobKbtEMnylZUKGCfAOBycTYA6vmk9jeZ/8QFC8UaXbPWyU8uguMZklw==
ARC-Message-Signature: i=1; a=rsa-sha256; c=relaxed/relaxed; d=microsoft.com;
 s=arcselector9901;
 h=From:Date:Subject:Message-ID:Content-Type:MIME-Version:X-MS-Exchange-AntiSpam-MessageData-ChunkCount:X-MS-Exchange-AntiSpam-MessageData-0:X-MS-Exchange-AntiSpam-MessageData-1;
 bh=8GOHbrHGAse+VwxwQ8bctFOzUmEf/xdtJgHt1uVZBJc=;
 b=mleTZ5VwJIKjzquYpDtDx+oSidi/fGVNMVgoo90D8OJinAQK/ii8nGXpQq0F06Yh7YYBISM3be3oyLJzauHLY49EJUl3i24v5Oyey3PhhHT25Y6nzxpg0ZanSaUtKJnTKORVfKYWcoB66Dy2asMPxlcv9HzIuMAMZ0aopZMz3sST4cl2zZ1WuTCJmIS5wW3qzribc2vMtq38k8Dj4mA/dVfkzy3xdgeUKGjjmEH4MRvCHscINgt/wcf4WjDX+96jum/zHu91W2S4uxnRUh3sBbI2mon1UVZXhCT4s8lLBiWPlZ3mvVG15D/DYz9/np8EKEywZOn5tU/ZrnAj/P4Onw==
ARC-Authentication-Results: i=1; mx.microsoft.com 1; spf=none; dmarc=none
 action=none header.from=accountprotection.microsoft.com; dkim=none (message
 not signed); arc=none
DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed;
 d=accountprotection.microsoft.com; s=selector1;
 h=From:Date:Subject:Message-ID:Content-Type:MIME-Version:X-MS-Exchange-SenderADCheck;
 bh=8GOHbrHGAse+VwxwQ8bctFOzUmEf/xdtJgHt1uVZBJc=;
 b=DpCUlylyZDtcJn6djHmjEEazw/i/B60SO++9oRrvX8g9LxFxEut9iFsMvx+XQEvmj4do5V5YZH83ZCruDYX4kIA4+Qr3njAistFwFW/LpQ6IvCufRUn/xvJo+3E8xfOxncoKEER3ehZ1hjdOBKK+Sg2D7wjyuEPCrq3s1t4qmcQ=
Received: from DM5PR15CA0039.namprd15.prod.outlook.com (2603:10b6:4:4b::25) by
 MW3PR16MB3756.namprd16.prod.outlook.com (2603:10b6:303:51::18) with Microsoft
 SMTP Server (version=TLS1_2, cipher=TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384) id
 15.20.4690.26; Wed, 17 Nov 2021 10:25:45 +0000
Received: from DM6NAM11FT021.eop-nam11.prod.protection.outlook.com
 (2603:10b6:4:4b:cafe::26) by DM5PR15CA0039.outlook.office365.com
 (2603:10b6:4:4b::25) with Microsoft SMTP Server (version=TLS1_2,
 cipher=TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384) id 15.20.4713.19 via Frontend
 Transport; Wed, 17 Nov 2021 10:25:44 +0000
X-MS-Exchange-Authentication-Results: spf=none (sender IP is 52.188.222.33)
 smtp.mailfrom=accountprotection.microsoft.com; dkim=none (message not signed)
 header.d=none;dmarc=none action=none
 header.from=accountprotection.microsoft.com;
Received: from accountprotection.microsoft.com (52.188.222.33) by
 DM6NAM11FT021.mail.protection.outlook.com (10.13.173.76) with Microsoft SMTP
 Server (version=TLS1_2, cipher=TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384) id
 15.20.4690.15 via Frontend Transport; Wed, 17 Nov 2021 10:25:44 +0000
From: Equipo de cuentas Microsoft
	<account-security-noreply@accountprotection.microsoft.com>
Date: Wed, 17 Nov 2021 02:25:44 -0800
Subject: =?iso-8859-1?q?Verificaci=F3n_de_la_informaci=F3n?= de seguridad de
 la cuenta Microsoft
To: javier.artiga@outlook.com
X-MSAPipeline: MessageDispatcherEOP
Message-ID: <2KW3QVDEBFU4.9C2CC499N6CS@BL02EPF00001955>
X-MSAMetaData:
 =?us-ascii?q?DRYxILKSZ!FhtgU0!y!ITlMlKusgM5c4YoL6!*FhbFGnsO7IIFvXOGXIwepm*?=
 =?us-ascii?q?7AFlhWQaVJ22hzdP!3oycgjKlMKyd!8fQPmDj9A9mXEJE3OsbILX2S67vQ4OH?=
 =?us-ascii?q?ScgdQnjQ$$?=
Content-Type: multipart/alternative; boundary="=-R18SRIndcri8wVr7SiC8Yw=="
Return-Path: account-security-noreply@accountprotection.microsoft.com
X-MS-PublicTrafficType: Email
X-MS-Office365-Filtering-Correlation-Id: 9a9c147d-981a-4754-5cae-08d9a9b49ddc
X-MS-TrafficTypeDiagnostic:
 MW3PR16MB3756:FirstParty-MicrosoftAccount-V3-System|AM6PR0202MB3318:
X-Microsoft-Antispam-PRVS:
 <MW3PR16MB3756CF8FC39EAB343304E260899A9@MW3PR16MB3756.namprd16.prod.outlook.com>
X-MS-Oob-TLC-OOBClassifiers: OLM:1051;
X-MS-Exchange-SenderADCheck: 1
X-MS-Exchange-AntiSpam-Relay: 0
X-Microsoft-Antispam-Untrusted: BCL:0;
X-Microsoft-Antispam-Message-Info-Original:
 ihfOlae1FgPMvoYYp5KjUflVgurynk7oQZxNJRNbfXszaU6d3u7QE7iBgQH/Gp5tadJkdxra2KR/mO0uoSvZTJDYJHscSZ9xyaNQUseE80l7cNhsaI8G3LPPY+Vzu1VatXP1B4HOf9dhY68t22mEoPBporkZcC6ULqEEYl+0GR/cLmoM/k+rwY3KxSn2h+kjAnOe0Ap/9PMtYdV7UTz1Nd+CUsRn5UN2dlPc5exQPLRhcJBPOT1Bcri8OZNvMw3BiH6OjJe4QoZ1Sia0/M8yCxMiUzDUHGtZJwsqbb5xs87jYnV5DAu3ApzKhdFucerAohOc0FYPVavqC19GmO38gz6wBxNRUCuzniKPp8ipCyocoJzKRDDuGahUC4ggjg8AGKGARZfQw9TQxaLo4YfAqlB1rCRL3YVSYvqcpDf8gpeIAIQsVBIwobXOZSFKsRwy1WiGob4Q9l3IAmjlNn+cC7rBK+RvZcZiGoC7pGYzIVr3NMAAt4+YD44QgSvV/Qz0DP/6YBdh4mjQwHdZnyLaOXxxObhtyAOyAfhavks/NQqoZAS3vSA0XHs4ukhBYekudmOLvwkltotrR39NuC7rGKCcp5rBWsrhR135GLnL4Lrr09ncbq71KUoWPkXDUmzic2fM0Y6DLI40btY9u2WgjX4ZnyPns+meI4GIKVmNbvlF3JXB30aDw/X1hwQCsHfA9nrtvD9RPlFjUsItbmBJmoZqJS3ede+JGLQoW8MJ9qQGClRhh68ocNLffaK9kI/8
X-Forefront-Antispam-Report-Untrusted:
 CIP:52.188.222.33;CTRY:US;LANG:es;SCL:-1;SRV:;IPV:NLI;SFV:NSPM;H:accountprotection.microsoft.com;PTR:InfoDomainNonexistent;CAT:NONE;SFS:;DIR:OUT;SFP:1101;
X-MS-Exchange-AntiSpam-MessageData-Original-ChunkCount: 1
X-MS-Exchange-AntiSpam-MessageData-Original-0:
 cITXwdcNk2A4Mzpf1E7zVd+hmJLmwasSiXASCI0oP2azHsYkq4VwrHh2ujk7k62BnxIM2jKRPoFU/6AVTD285DjRHnE1CFJoC2r48AGIRHiESm7oU1wERLqhQPdcpbmWGoIsI7epkUvD2cO05wr6u/qYRDqs7343bdOlrJR3UN1pOLbubr405yDG3YmWr2hc+97md2xNoHPWmSLXVbyNX2Ek7FUWC6nRtLms9fFKQj++OIboercSeuz+jj8yVUMe
X-MS-Exchange-Transport-CrossTenantHeadersStamped: MW3PR16MB3756
X-IncomingHeaderCount: 40
X-MS-Exchange-Organization-ExpirationStartTime: 17 Nov 2021 10:25:45.7307
 (UTC)
X-MS-Exchange-Organization-ExpirationStartTimeReason: OriginalSubmit
X-MS-Exchange-Organization-ExpirationInterval: 1:00:00:00.0000000
X-MS-Exchange-Organization-ExpirationIntervalReason: OriginalSubmit
X-MS-Exchange-Organization-Network-Message-Id:
 9a9c147d-981a-4754-5cae-08d9a9b49ddc
X-EOPAttributedMessage: 0
X-EOPTenantAttributedMessage: 84df9e7f-e9f6-40af-b435-aaaaaaaaaaaa:0
X-MS-Exchange-Organization-MessageDirectionality: Incoming
X-MS-Exchange-Transport-CrossTenantHeadersStripped:
 DM6NAM12FT021.eop-nam12.prod.protection.outlook.com
X-MS-Exchange-Transport-CrossTenantHeadersPromoted:
 DM6NAM12FT021.eop-nam12.prod.protection.outlook.com
X-MS-Exchange-Organization-AuthSource:
 DM6NAM12FT021.eop-nam12.prod.protection.outlook.com
X-MS-Exchange-Organization-AuthAs: Anonymous
X-MS-UserLastLogonTime: 11/16/2021 11:24:23 AM
X-MS-Office365-Filtering-Correlation-Id-Prvs:
 3e6f14d5-06b0-47db-6bfc-08d9a9b49d37
X-MS-Exchange-EOPDirect: true
X-Sender-IP: 40.107.94.50
X-SID-PRA: ACCOUNT-SECURITY-NOREPLY@ACCOUNTPROTECTION.MICROSOFT.COM
X-SID-Result: PASS
X-MS-Exchange-Organization-PCL: 2
X-MS-Exchange-Organization-SCL: -1
X-Microsoft-Antispam: BCL:0;
X-MS-Exchange-CrossTenant-OriginalArrivalTime: 17 Nov 2021 10:25:45.6908
 (UTC)
X-MS-Exchange-CrossTenant-Network-Message-Id: 9a9c147d-981a-4754-5cae-08d9a9b49ddc
X-MS-Exchange-CrossTenant-Id: 84df9e7f-e9f6-40af-b435-aaaaaaaaaaaa
X-MS-Exchange-CrossTenant-OriginalAttributedTenantConnectingIp: TenantId=5ba90553-c2cd-460e-b5fd-ab93ad9155c7;Ip=[52.188.222.33];Helo=[accountprotection.microsoft.com]
X-MS-Exchange-CrossTenant-AuthSource:
 DM6NAM12FT021.eop-nam12.prod.protection.outlook.com
X-MS-Exchange-CrossTenant-AuthAs: Anonymous
X-MS-Exchange-CrossTenant-FromEntityHeader: Internet
X-MS-Exchange-CrossTenant-RMS-PersistedConsumerOrg:
 00000000-0000-0000-0000-000000000000
X-MS-Exchange-Transport-CrossTenantHeadersStamped: AM6PR0202MB3318
X-MS-Exchange-Transport-EndToEndLatency: 00:00:01.4706834
X-MS-Exchange-Processed-By-BccFoldering: 15.20.4713.020
X-Microsoft-Antispam-Mailbox-Delivery:
	abwl:0;wl:0;pcwl:0;kl:0;iwl:0;dwl:0;dkl:0;rwl:0;ucf:0;jmr:0;ex:0;auth:1;dest:I;OFR:SpamFilterPass;ENG:(5062000284)(90000117)(90010023)(91010020)(91040095)(5061607266)(5061608174)(9050020)(9100337)(4900116)(4910009)(9910002)(9520004)(9320001)(9235001)(4920091)(6212095)(4960005)(4950132)(4990091)(9110004);
X-Message-Info:
	5vMbyqxGkdee9CWP6GN6k5gExbIfNaICJcGQMT0W3r/houUwUw/zqDaB+WoOtgVTsE7k0luqkz/Yy0NN2G2cChUj6StQFCAMokoCsak3ycsmpNEVUERQ2E/qXpW96+DERl58B7wcEAJrrJQl+WXsDpb6p86BVqZjsyFHukgawqRwlVAOdS/XKdaulYpj8fWM5zwAp1aijvcMUReMMMH9Pw==
X-Message-Delivery: Vj0xLjE7dXM9MDtsPTA7YT0xO0Q9MTtHRD0xO1NDTD0tMQ==
X-Microsoft-Antispam-Message-Info:
	=?utf-8?B?WUp4UmhlL3hQNkRTVG1UQ2FSZzh6MEJldVhZN25ZYjBkUlVnRkNiMVFzVnhH?=
 =?utf-8?B?S1p5dk9pb3hET0pLK3MvM041a29rQ3orc3pieENiS3RyaXo2eUE0SE5QeGN2?=
 =?utf-8?B?MGV2N2ZrdUsvUHBFQ0YxQmw0dWxQZ3Vib3hwK1BCZEdpSXNtSWErWHlNMHcz?=
 =?utf-8?B?R0ZGK01KUDVMWSsweVMyY29LQmxteG02UlkyL3kza1EydVphU2U2UkJ3NWNG?=
 =?utf-8?B?azMreWtEM2RLR2FDOXV5WU5RSk9aSmpDRE85aWlSSkFmb1B6b3ZjbVd5V0lL?=
 =?utf-8?B?YWgrOUwydm5NSHpPQmZ4ZnROTHRrWEtvVnJFbWJKZG15SFpBRXhWaVpMaWlH?=
 =?utf-8?B?cFZORmJRZGcvYWszVm5xcUkxL0Y1dUE4Y0lsZWdiY1lvTGhiQ0dRVk9oTk5R?=
 =?utf-8?B?Rm5ReTlYeUtjNTlmZEl5SFY2V2tzNXJ2aXZpUGhNQWNROHlFdTNtVk5WOUwr?=
 =?utf-8?B?eEFISTJvK2hGWnhHRnB6V0wyaUpCOVNWdFJpWk1HUE9OdEdnS1B1RE1GNjFh?=
 =?utf-8?B?dklKVjdZOVd1WUlBd1hLSy9YQkgrNzBVbW5GT1BxUzBrRlNTVmxDS29uSUpw?=
 =?utf-8?B?YzZHQnlEczljdzh4UG9BRi91WDlYQ08wTXpHakFXNWJQVlA0Y3AxNVpwWEZO?=
 =?utf-8?B?cTFrU2RBV0Rwc2Q0eVJzN0Y2eHoxREI2cFYzeWlzNDRtRkZrbTZNMXVSUWkr?=
 =?utf-8?B?a2VZVUR5bVlIMGdXTUVGdDM4NkJ6NXVUeFY5Qk9SRkVkOVpFcFlKb1hLaHdk?=
 =?utf-8?B?MXl5cmx6TjVlR0pLS0sycDlZYkcrVWc5Wkl6MHVCTGx4OTVobUJtS0FqVnFJ?=
 =?utf-8?B?dFNWZE56WmRGNlpERUpCSGJFbXRGWWZPNkIwWnYrZlpBVmVkbDE1djlnUjZr?=
 =?utf-8?B?YVNYMU1qSHlhWVZlMWdpTm0zcTgwWjV5cUNIZVN0QnljU1RLc29HS3pQcmdm?=
 =?utf-8?B?MWIvZ3l0Q2c0MXRlOG5pVDJLY2pUalN5VFBhSFpORDRMVmg0amhmQkZaT2E4?=
 =?utf-8?B?aUpzQnBBa2p4bGdlUzRlenUwZVZlUzRJMTEzcGNYajVhMWFtS1dZQ1luQy9O?=
 =?utf-8?B?Z3FGU3ZRWE9KZUhKWWxpQUhFWE5WcmhuL0N6QysvcThHdU05ZUFzc2QrWk9B?=
 =?utf-8?B?bEtUck05TmhaaityQ0tQQUtFSG1oRVV1bi9SejlhTStJaDhYM1hYbjM2WFMy?=
 =?utf-8?B?OEwwNUV6VWNKREZzdDJPYThqYUlkNlpFRHJ2NHZHQzc5bGNWY1ZPYlRJQXl6?=
 =?utf-8?B?WWpINzVTaGRxT0dUdTRjTHF1b3dFdXQrWmxwVlY0Vk5VR0tydXpnZnFhMWdm?=
 =?utf-8?B?UGFsSld1UWNMaXBmTE1uQmloZEI0RUZNR3dMUkd3RGsyT3Ryc2NzTUJXRUdw?=
 =?utf-8?B?OEluQnZKWEtWZXVUYTBaOVJsZmVUUmxVdUpSRDhhbnptNnpIdld6UW96by8w?=
 =?utf-8?B?OTZQQlpObXptanJiWmZ1UGowYUdRL290emtvNnFoUjN5QnNOak92Z3pPYy92?=
 =?utf-8?B?MUdMbjB1d3JDMHBCdDJMSDFEL2Q5MHdsMFJDRU80NGxqZ0xRbzZBaXhOYVQy?=
 =?utf-8?B?YTNGZlI5L3VpRWJGbXJUbUhmK1IzRFMxd2xFWUMyR1dSU3FhSHRpMEtlcUVT?=
 =?utf-8?B?ZzRiVkZsMlBQUVNGVDhHczdOVytuOXJnbnBNZXhDSUxRcFhtTEhsY01YY1kz?=
 =?utf-8?B?dENMMHNWZTJtRlM4WThlS3Z2L0t6V2RBTnNYMFNRbnd6SUs4TXZFZkxoT2Rt?=
 =?utf-8?B?VUlJVGRIZDdpWFZTbWtYQm1DMUFCVVBqcHkwTmpxRDZzN1JSU0lDNHMrOWdi?=
 =?utf-8?B?bUdhdkVxblBIcU9aTVBES3hPOUpmYkI4cndmZnpGd3pjaHhhajEwNm5iSEI0?=
 =?utf-8?B?ZDkrTW5LcTh0cDgwdk1sTW5oRzhVdDdXM3lhdVNnRmFLSXFTK0RqclN5ZFlu?=
 =?utf-8?B?LzRuSjd2UXRnRHhaeCtjbmtkVDN3M1NTOHpkQUQyUndqRmpTTUhjSU5hTUJU?=
 =?utf-8?B?NytBNkpvd2hRQW9NTjNSSHhNRUlZQlVlTFJhSE5vOTBFY1EvVzNQMGZLODdX?=
 =?utf-8?B?Vzc3QlgwejNqWU12TWs1VEp3Z1hITDBqWmpxdz09?=
MIME-Version: 1.0

--=-R18SRIndcri8wVr7SiC8Yw==
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit

Recientemente comprobaste la informaciÃ³n de seguridad de la cuenta Microsoft ja**a@outlook.com. Esto fue una comprobaciÃ³n de seguridad periÃ³dica que solo ocurre si Ãºltimamente no has usado un cÃ³digo de seguridad. No necesitarÃ¡s proporcionar un cÃ³digo cada vez que inicies sesiÃ³n.

Es importante que la informaciÃ³n de seguridadÂ asociada a tu cuenta se mantenga correcta y actualizada. Nunca usaremos esta informaciÃ³n para enviarte correo no deseadoÂ ni para fines de marketing. Solo se usa para comprobar tu identidad si hay algÃºn problema con tu cuenta.

Para obtener mÃ¡s informaciÃ³n o para ponerte en contacto conÂ el servicio tÃ©cnico, haz clic aquÃ­ http://go.microsoft.com/fwlink/?LinkID=281822.

Para no participar o para cambiar dÃ³nde debes recibir notificaciones de seguridad, haz clic aquÃ­ https://account.live.com/SecurityNotifications/Update.

Gracias,
El equipo de cuentas Microsoft 
--=-R18SRIndcri8wVr7SiC8Yw==
Content-Type: text/html; charset=utf-8
Content-Transfer-Encoding: 8bit

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><html xmlns="http://www.w3.org/1999/xhtml" dir="ltr"><head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"><style type="text/css">
 .link:link, .link:active, .link:visited {
       color:#2672ec !important;
       text-decoration:none !important;
 }

 .link:hover {
       color:#4284ee !important;
       text-decoration:none !important;
 }
</style>
<title></title>
</head>
<body>
<table dir="ltr">
      <tr><td id="i1" style="padding:0; font-family:'Segoe UI Semibold', 'Segoe UI Bold', 'Segoe UI', 'Helvetica Neue Medium', Arial, sans-serif; font-size:17px; color:#707070;">Cuenta Microsoft</td></tr>
      <tr><td id="i2" style="padding:0; font-family:'Segoe UI Light', 'Segoe UI', 'Helvetica Neue Medium', Arial, sans-serif; font-size:41px; color:#2672ec;">Gracias por comprobar tu informaciÃ³n de seguridad</td></tr>
      <tr><td id="i3" style="padding:0; padding-top:25px; font-family:'Segoe UI', Tahoma, Verdana, Arial, sans-serif; font-size:14px; color:#2a2a2a;">Recientemente comprobaste la informaciÃ³n de seguridad de tu cuenta Microsoft <a dir="ltr" id="iAccount" class="link" style="color:#2672ec; text-decoration:none" href="mailto:ja**a@outlook.com">ja**a@outlook.com</a>. Esto fue una comprobaciÃ³n de seguridad periÃ³dica que solo ocurre si Ãºltimamente no has usado un cÃ³digo de seguridad. No necesitarÃ¡s proporcionar un cÃ³digo cada vez que inicies sesiÃ³n.</td></tr>
      <tr><td id="i4" style="padding:0; padding-top:25px; font-family:'Segoe UI', Tahoma, Verdana, Arial, sans-serif; font-size:14px; color:#2a2a2a;">Es importante que la informaciÃ³n de seguridad asociada a tu cuenta se mantenga correcta y actualizada. Nunca usaremos esta informaciÃ³n para enviarte correo no deseado ni para fines de marketing. Solo se usa para comprobar tu identidad si hay algÃºn problema con tu cuenta.</td></tr>
      <tr><td id="i5" style="padding:0; padding-top:25px; font-family:'Segoe UI', Tahoma, Verdana, Arial, sans-serif; font-size:14px; color:#2a2a2a;">Para obtener mÃ¡s informaciÃ³n o para ponerte en contacto con el soporte tÃ©cnico, <a id="iLink1" class="link" style="color:#2672ec; text-decoration:none" href="http://go.microsoft.com/fwlink/?LinkID=281822">haz clic aquÃ­</a>.</td></tr>
      <tr><td id="i6" style="padding:0; padding-top:25px; font-family:'Segoe UI', Tahoma, Verdana, Arial, sans-serif; font-size:14px; color:#2a2a2a;">Para no participar o para cambiar cuÃ¡ndo debes recibir notificaciones de seguridad, <a id="iLink2" class="link" style="color:#2672ec; text-decoration:none" href="https://account.live.com/SecurityNotifications/Update">haz clic aquÃ­</a>.</td></tr>
      <tr><td id="i7" style="padding:0; padding-top:25px; font-family:'Segoe UI', Tahoma, Verdana, Arial, sans-serif; font-size:14px; color:#2a2a2a;">Gracias,</td></tr>
      <tr><td id="i8" style="padding:0; font-family:'Segoe UI', Tahoma, Verdana, Arial, sans-serif; font-size:14px; color:#2a2a2a;">El equipo de cuentas Microsoft</td></tr>
</table>
</body>
</html>
--=-R18SRIndcri8wVr7SiC8Yw==--\
"""

def test_get_content_from_base64_payload():
    msg = email.message_from_string(payload, policy=default_policy)

    assert extract_body_from_email_message(msg, remove_html_tags=True)[:66]=="Recientemente comprobaste la información de seguridad de la cuenta"
