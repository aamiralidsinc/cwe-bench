# H1 / H2 groups: co-present advisories split by how upstream fixed them

Packages with 2+ co-present, non-DoS advisories that carry fix commits: 2071. H1 (all fixed together) 169, H2 (all fixed separately) 1558, mixed 344.

Mid-size groups (3-8 co-present, the useful zone): 916; by pattern: H2 652, H1+H2 213, H1 51.

| Package | Repo | Co-present | Fixed together | Distinct fix commits | Pattern | CWEs |
|---|---|---|---|---|---|---|
| Maven:org.jenkins-ci.plugins:config-file-provider | jenkinsci/config-file-provider-plugin | 8 | 2 | 7 | H1+H2 | CWE-352;CWE-611;CWE-79;CWE-862;CWE-863 |
| PyPI:hermes-agent | nousresearch/hermes-agent | 8 | 2 | 7 | H1+H2 | CWE-269,CWE-526;CWE-276;CWE-306;CWE-697;CWE-74 |
| PyPI:keras | keras-team/keras | 8 | 2 | 7 | H1+H2 | CWE-200,CWE-73;CWE-22;CWE-502;CWE-502,CWE-918;CWE-94 |
| PyPI:mindsdb | mindsdb/mindsdb | 8 | 6 | 4 | H1+H2 | CWE-20;CWE-22;CWE-350,CWE-918;CWE-918;CWE-94,CWE-95 |
| PyPI:indico | indico/indico | 8 | 2 | 11 | H1+H2 | CWE-1395,CWE-79;CWE-22,CWE-78;CWE-367,CWE-918;CWE-692;CWE-79 |
| PyPI:zenml | zenml-io/zenml | 8 | 2 | 7 | H1+H2 | CWE-1021;CWE-1220,CWE-862;CWE-287,CWE-620;CWE-29;CWE-362,CWE |
| PyPI:docling-slim | docling-project/docling | 8 | 2 | 7 | H1+H2 | CWE-1188,CWE-22,CWE-73;CWE-200,CWE-73;CWE-201,CWE-522;CWE-36 |
| PyPI:roundup | roundup-tracker/roundup | 8 | 3 | 8 | H1+H2 | CWE-284;CWE-79 |
| Go:gitea.dev | go-gitea/gitea | 8 | 4 | 8 | H1+H2 | CWE-200,CWE-863;CWE-280,CWE-863;CWE-284,CWE-400;CWE-639,CWE- |
| Go:github.com/gofiber/fiber/v2 | gofiber/fiber | 8 | 2 | 10 | H1+H2 | CWE-20;CWE-290;CWE-338;CWE-346;CWE-352;CWE-384;CWE-670;CWE-7 |
| Go:github.com/apache/incubator-answer | apache/answer | 8 | 2 | 7 | H1+H2 | CWE-200;CWE-326;CWE-359;CWE-434;CWE-772;CWE-79,CWE-80 |
| Packagist:smarty/smarty | smarty-php/smarty | 8 | 4 | 12 | H1+H2 | CWE-20;CWE-22;CWE-22,CWE-61;CWE-79;CWE-918;CWE-94 |
| Packagist:phpoffice/phpspreadsheet | phpoffice/phpspreadsheet | 8 | 7 | 6 | H1+H2 | CWE-79 |
| Packagist:starcitizentools/citizen-skin | starcitizentools/mediawiki-skins-citizen | 8 | 7 | 10 | H1+H2 | CWE-79 |
| Packagist:redaxo/source | redaxo/core | 8 | 4 | 6 | H1+H2 | CWE-20,CWE-200;CWE-352;CWE-434;CWE-79 |
| crates.io:rusqlite | rusqlite/rusqlite | 8 | 2 | 7 | H1+H2 | CWE-134;CWE-351;CWE-362;CWE-416 |
| crates.io:tough | awslabs/tough | 8 | 2 | 7 | H1+H2 | CWE-1025;CWE-1288;CWE-22;CWE-347;CWE-670 |
| npm:@lobehub/chat | lobehub/lobe-chat | 8 | 2 | 7 | H1+H2 | CWE-284;CWE-601;CWE-73;CWE-79;CWE-918 |
| npm:electerm | electerm/electerm | 8 | 4 | 8 | H1+H2 | CWE-20,CWE-829,CWE-94;CWE-22;CWE-326,CWE-329,CWE-353,CWE-759 |
| npm:multer | expressjs/multer | 8 | 2 | 7 | H1+H2 | CWE-248;CWE-362;CWE-401;CWE-459;CWE-772 |
| npm:elliptic | indutny/elliptic | 8 | 3 | 8 | H1+H2 | CWE-130;CWE-190;CWE-200;CWE-327;CWE-347 |
| npm:@backstage/plugin-techdocs-node | backstage/backstage | 8 | 2 | 12 | H1+H2 | CWE-1336,CWE-94;CWE-183,CWE-470;CWE-22;CWE-22,CWE-59;CWE-22, |
| Maven:org.cloudfoundry.identity:cloudfoundry-identity-server | cloudfoundry/uaa | 8 | 0 | 22 | H2 | CWE-352;CWE-613;CWE-640 |
| Maven:org.yamcs:yamcs-core | yamcs/yamcs | 8 | 0 | 15 | H2 | CWE-1336,CWE-470,CWE-94;CWE-22;CWE-284,CWE-862;CWE-285,CWE-8 |
| Maven:org.xwiki.platform:xwiki-platform-oldcore | xwiki/xwiki-platform | 8 | 0 | 13 | H2 | CWE-22,CWE-24;CWE-274;CWE-400,CWE-787;CWE-601;CWE-79;CWE-862 |
| Maven:tools.jackson.core:jackson-databind | fasterxml/jackson-databind | 8 | 0 | 13 | H2 | CWE-184;CWE-184,CWE-502;CWE-863;CWE-915;CWE-918 |
| Maven:com.rabbitmq:amqp-client | rabbitmq/rabbitmq-java-client | 8 | 0 | 13 | H2 | CWE-172,CWE-248;CWE-20;CWE-295;CWE-470;CWE-509;CWE-789;CWE-8 |
| PyPI:dulwich | jelmer/dulwich | 8 | 0 | 9 | H2 | CWE-22;CWE-22,CWE-59;CWE-59,CWE-61;CWE-78;CWE-835 |
| PyPI:torch | pytorch/pytorch | 8 | 0 | 9 | H2 | CWE-119;CWE-122;CWE-404;CWE-416;CWE-502;CWE-77 |
| PyPI:notebook | jupyter/notebook | 8 | 0 | 13 | H2 | CWE-20;CWE-601;CWE-79 |
| PyPI:glance | openstack/glance | 8 | 0 | 20 | H2 | CWE-200;CWE-22;CWE-532;CWE-918 |
| PyPI:pip | pypa/pip | 8 | 0 | 8 | H2 | CWE-20;CWE-22;CWE-36;CWE-59;CWE-77;CWE-829 |
| Go:github.com/rabbitmq/amqp091-go | rabbitmq/amqp091-go | 8 | 0 | 8 | H2 | CWE-116;CWE-190;CWE-195;CWE-316;CWE-316,CWE-326;CWE-681;CWE- |
| Go:github.com/go-gitea/gitea | go-gitea/gitea | 8 | 0 | 10 | H2 | CWE-200;CWE-284;CWE-294 |
| Go:github.com/enchant97/note-mark/backend | enchant97/note-mark | 8 | 0 | 8 | H2 | CWE-20,CWE-22;CWE-200,CWE-285;CWE-208;CWE-285;CWE-287;CWE-32 |
| Go:github.com/opencontainers/runc | opencontainers/runc | 8 | 0 | 14 | H2 | CWE-190;CWE-200;CWE-22,CWE-362,CWE-367;CWE-269;CWE-276;CWE-2 |
| Packagist:pimcore/customer-management-framework-bundle | pimcore/customer-data-framework | 8 | 0 | 8 | H2 | CWE-1236;CWE-20;CWE-257,CWE-522;CWE-284;CWE-285,CWE-863;CWE- |
| Packagist:kevinpapst/kimai2 | kevinpapst/kimai2 | 8 | 0 | 8 | H2 | CWE-1236;CWE-284,CWE-639,CWE-863;CWE-352;CWE-79 |
| Packagist:ssddanbrown/bookstack | bookstackapp/bookstack | 8 | 0 | 8 | H2 | CWE-284;CWE-284,CWE-668,CWE-863;CWE-284,CWE-79;CWE-284,CWE-8 |
| npm:fastify | fastify/fastify | 8 | 0 | 8 | H2 | CWE-1287;CWE-178;CWE-20;CWE-248;CWE-288;CWE-348 |
