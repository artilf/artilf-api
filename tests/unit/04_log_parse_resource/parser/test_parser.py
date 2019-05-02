import json
from parser import (enqueue, get_log_data, json_iter_load, parse_log_data,
                    validate_and_get_s3_object_info)

import pytest


class TestValidateAndGetS3ObjectInfo(object):
    @pytest.mark.parametrize(
        'queue_url, error', [
            (1, TypeError),
            ('', ValueError)
        ]
    )
    def test_exception_queue_url(self, queue_url, error):
        with pytest.raises(error):
            validate_and_get_s3_object_info(None, queue_url)

    @pytest.mark.parametrize(
        'event, error', [
            (
                None,
                TypeError
            ),
            (
                {},
                KeyError
            ),
            (
                {'Records': 1},
                TypeError
            ),
            (
                {
                    'Records': [
                        1
                    ]
                },
                TypeError
            ),
            (
                {
                    'Records': [
                        {
                            's3': {
                                'bucket': 1
                            }
                        }
                    ]
                },
                TypeError
            ),
            (
                {
                    'Records': [
                        {
                            's3': {
                                'bucket': {'name': 1},
                                'object': {'key': 'aaa'}
                            }
                        }
                    ]
                },
                TypeError
            ),
            (
                {
                    'Records': [
                        {
                            's3': {
                                'bucket': {'name': ''},
                                'object': {'key': 'aaa'}
                            }
                        }
                    ]
                },
                ValueError
            ),
            (
                {
                    'Records': [
                        {
                            's3': {
                                'bucket': {'name': 'aaa'},
                                'object': {'key': 1}
                            }
                        }
                    ]
                },
                TypeError
            ),
            (
                {
                    'Records': [
                        {
                            's3': {
                                'bucket': {'name': 'aaa'},
                                'object': {'key': ''}
                            }
                        }
                    ]
                },
                ValueError
            ),
            (
                {
                    'Records': [
                        {
                            's3': {
                                'bucket': {'name': 'aaa'},
                                'object': {'key': 'bbb'}
                            }
                        },
                        {
                            's3': {
                                'bucket': {'name': 'aaa'},
                                'object': {'key': ''}
                            }
                        }
                    ]
                },
                ValueError
            )
        ]
    )
    def test_exception_event(self, event, error):
        with pytest.raises(error):
            validate_and_get_s3_object_info(event, 'a')

    @pytest.mark.parametrize(
        'event, expected', [
            (
                {
                    'Records': [
                        {
                            's3': {
                                'bucket': {'name': 'aaa'},
                                'object': {'key': 'bbb'}
                            }
                        },
                        {
                            's3': {
                                'bucket': {'name': 'aaa'},
                                'object': {'key': 'ccc'}
                            }
                        }
                    ]
                },
                [
                    {
                        'Bucket': 'aaa',
                        'Key': 'bbb'
                    },
                    {
                        'Bucket': 'aaa',
                        'Key': 'ccc'
                    }
                ]
            )
        ]
    )
    def test_normal(self, event, expected):
        actual = validate_and_get_s3_object_info(event, 'a')
        assert actual == expected


class TestJsonIterLoad(object):
    @pytest.mark.parametrize(
        'text, expected', [
            (
                '\n'.join([
                    json.dumps({'a': 1, 'bb': True}),
                    json.dumps({'ccc': 'chronicle'})
                ]),
                [
                    {'a': 1, 'bb': True},
                    {'ccc': 'chronicle'}
                ]
            ),
            (
                ''.join([
                    json.dumps({'a': 1, 'bb': True}),
                    json.dumps({'ccc': 'chronicle'})
                ]),
                [
                    {'a': 1, 'bb': True},
                    {'ccc': 'chronicle'}
                ]
            )
        ]
    )
    def test_normal(self, text, expected):
        actual = list(json_iter_load(text))
        assert actual == expected


class TestGetLogData(object):
    @pytest.mark.parametrize(
        'create_s3_bucket, s3_put_gz_files, s3_object, expected', [
            (
                'test_bucket',
                {
                    'bucket': 'test_bucket',
                    'objects': [
                        {
                            'key': 'sakura_wars',
                            'body': '\n'.join([
                                json.dumps({'number': 1, 'sub': '熱き血潮に'}),
                                json.dumps({'number': 2, 'sub': '君、死にたもうことなかれ'}),
                                json.dumps({'number': 3, 'sub': '巴里は燃えているか'}),
                                json.dumps({'number': 4, 'sub': '恋せよ乙女'}),
                                json.dumps({'number': 5, 'sub': 'さらば愛しき人よ'})
                            ])
                        }
                    ]
                },
                {
                    'Bucket': 'test_bucket',
                    'Key': 'sakura_wars'
                },
                [
                    {'number': 1, 'sub': '熱き血潮に'},
                    {'number': 2, 'sub': '君、死にたもうことなかれ'},
                    {'number': 3, 'sub': '巴里は燃えているか'},
                    {'number': 4, 'sub': '恋せよ乙女'},
                    {'number': 5, 'sub': 'さらば愛しき人よ'}
                ]
            )
        ], indirect=['create_s3_bucket', 's3_put_gz_files']
    )
    @pytest.mark.usefixtures('create_s3_bucket', 's3_put_gz_files')
    def test_normal(self, s3, s3_object, expected):
        actual = get_log_data(s3_object, s3)
        assert actual == expected


class TestParseLogData(object):
    @pytest.mark.parametrize(
        'log_data, expected', [
            (
                [
                    {
                        'logGroup': 'test_group',
                        'logStream': 'test_stream',
                        'logEvents': [
                            {
                                'timestamp': 1551144806145,
                                'message': ''
                            }
                        ]
                    }
                ],
                []
            ),
            (
                [
                    {
                        'logGroup': 'test_group',
                        'logStream': 'test_stream',
                        'logEvents': [
                            {
                                'timestamp': 1551144806145,
                                'message': '{"levelname": "ERROR"}'
                            }
                        ]
                    }
                ],
                [
                    {
                        'logGroup': 'test_group',
                        'logStream': 'test_stream',
                        'datetime': '2019-02-26 10:33:26.145000+09:00',
                        'message': '{"levelname": "ERROR"}',
                        'request_id': None
                    }
                ]
            ),
            (
                [
                    {
                        'logGroup': 'test_group',
                        'logStream': 'test_stream',
                        'logEvents': [
                            {
                                'timestamp': 1551144806145,
                                'message': '{"levelname": "ERROR", "lambda_request_id": "test_id"}'
                            },
                            {
                                'timestamp': 1551144236145,
                                'message': '{"levelname": "ERROR"}'
                            }
                        ]
                    }
                ],
                [
                    {
                        'logGroup': 'test_group',
                        'logStream': 'test_stream',
                        'datetime': '2019-02-26 10:33:26.145000+09:00',
                        'message': '{"levelname": "ERROR", "lambda_request_id": "test_id"}',
                        'request_id': 'test_id'
                    },
                    {
                        'logGroup': 'test_group',
                        'logStream': 'test_stream',
                        'datetime': '2019-02-26 10:23:56.145000+09:00',
                        'message': '{"levelname": "ERROR"}',
                        'request_id': None
                    }
                ]
            ),
            (
                [
                    {
                        'logGroup': 'test_group',
                        'logStream': 'test_stream',
                        'logEvents': [
                            {
                                'timestamp': 1551144806145,
                                'message': '{"levelname": "ERROR"}'
                            }
                        ]
                    },
                    {
                        'logGroup': 'test_group_02',
                        'logStream': 'test_stream_02',
                        'logEvents': [
                            {
                                'timestamp': 1551144806145,
                                'message': '{"levelname": "ERROR"}'
                            }
                        ]
                    }
                ],
                [
                    {
                        'logGroup': 'test_group',
                        'logStream': 'test_stream',
                        'datetime': '2019-02-26 10:33:26.145000+09:00',
                        'message': '{"levelname": "ERROR"}',
                        'request_id': None
                    },
                    {
                        'logGroup': 'test_group_02',
                        'logStream': 'test_stream_02',
                        'datetime': '2019-02-26 10:33:26.145000+09:00',
                        'message': '{"levelname": "ERROR"}',
                        'request_id': None
                    }
                ]
            )
        ]
    )
    def test_normal(self, log_data, expected):
        actual = parse_log_data(log_data)
        assert actual == expected


class TestEnqueue(object):
    @pytest.mark.parametrize(
        'alert_data, expected', [
            (
                [
                    {'test': 'data'}
                ],
                {'test': 'data'}
            )
        ]
    )
    def test_single(self, sqs, create_sqs_queue, alert_data, expected):
        enqueue(alert_data, create_sqs_queue, sqs)

        resp = sqs.receive_message(
            QueueUrl=create_sqs_queue
        )

        actual = resp['Messages'][0]['Body']
        assert json.loads(actual) == expected

    @pytest.mark.parametrize(
        'alert_data', [
            (
                [
                    {'title': '黄昏色の詠使い', 'number': 1, 'subtitle': 'イヴは夜明けに微笑んで'},
                    {'title': '黄昏色の詠使い', 'number': 2, 'subtitle': '奏でる少女の道行きは'},
                    {'title': '黄昏色の詠使い', 'number': 3, 'subtitle': 'アマデウスの詩、謳え敗者の王'},
                    {'title': '黄昏色の詠使い', 'number': 4, 'subtitle': '踊る世界、イヴの調律'},
                    {'title': '黄昏色の詠使い', 'number': 5, 'subtitle': '全ての歌を夢見る子供たち'},
                    {'title': '黄昏色の詠使い', 'number': 6, 'subtitle': 'そしてシャオの福音来たり'},
                    {'title': '黄昏色の詠使い', 'number': 7, 'subtitle': '新約の扉　汝ミクヴァの洗礼よ'},
                    {'title': '黄昏色の詠使い', 'number': 8, 'subtitle': '百億の星にリリスは祈り'},
                    {'title': '黄昏色の詠使い', 'number': 9, 'subtitle': 'ソフィア、詠と絆と涙を抱いて'},
                    {'title': '黄昏色の詠使い', 'number': 10, 'subtitle': '夜明け色の詠使い'},
                ]
            )
        ]
    )
    def test_multi(self, sqs, create_sqs_queue, alert_data):
        enqueue(alert_data, create_sqs_queue, sqs)

        resp = sqs.receive_message(
            QueueUrl=create_sqs_queue,
            MaxNumberOfMessages=10
        )
        ordered = []
        for message in resp['Messages']:
            body = json.loads(message['Body'])
            flag = False
            for i, data in enumerate(alert_data):
                if body == data:
                    flag = True
                    ordered.append(i)
                    break
            assert flag

        for i in range(10):
            assert i in ordered

    @pytest.mark.parametrize(
        'alert_data', [
            (
                [
                    {'title': 'SHIROBAKO', 'number': '#01', 'subtitle': '明日に向かって、えくそだすっ！'},
                    {'title': 'SHIROBAKO', 'number': '#02', 'subtitle': 'あるぴんはいます！'},
                    {'title': 'SHIROBAKO', 'number': '#03', 'subtitle': '総集編はもういやだ'},
                    {'title': 'SHIROBAKO', 'number': '#04', 'subtitle': '私ゃ失敗こいちまってさ'},
                    {'title': 'SHIROBAKO', 'number': '#05', 'subtitle': '人のせいにしているようなヤツは辞めちまえ！'},
                    {'title': 'SHIROBAKO', 'number': '#06', 'subtitle': 'イデポン宮森 発動篇'},
                    {'title': 'SHIROBAKO', 'number': '#07', 'subtitle': 'ネコでリテイク'},
                    {'title': 'SHIROBAKO', 'number': '#08', 'subtitle': '責めてるんじゃないからね'},
                    {'title': 'SHIROBAKO', 'number': '#09', 'subtitle': '何を伝えたかったんだと思う？'},
                    {'title': 'SHIROBAKO', 'number': '#10', 'subtitle': 'あと一杯だけね'},
                    {'title': 'SHIROBAKO', 'number': '#11', 'subtitle': '原画売りの少女'},
                    {'title': 'SHIROBAKO', 'number': '#12', 'subtitle': 'えくそだす・クリスマス'},
                    {'title': 'SHIROBAKO', 'number': '#13', 'subtitle': '好きな雲って何ですか？'},
                    {'title': 'SHIROBAKO', 'number': '#14', 'subtitle': '仁義なきオーディション会議！'},
                    {'title': 'SHIROBAKO', 'number': '#15', 'subtitle': 'こんな絵でいいんですか？'},
                    {'title': 'SHIROBAKO', 'number': '#16', 'subtitle': 'ちゃぶだい返し'},
                    {'title': 'SHIROBAKO', 'number': '#17', 'subtitle': '私どこにいるんでしょうか…'},
                    {'title': 'SHIROBAKO', 'number': '#18', 'subtitle': '俺をはめやがったな！'},
                    {'title': 'SHIROBAKO', 'number': '#19', 'subtitle': '釣れますか？'},
                    {'title': 'SHIROBAKO', 'number': '#20', 'subtitle': 'がんばりマスタング！'},
                    {'title': 'SHIROBAKO', 'number': '#21', 'subtitle': 'クオリティを人質にすんな'},
                    {'title': 'SHIROBAKO', 'number': '#22', 'subtitle': 'ノアは下着です。'},
                    {'title': 'SHIROBAKO', 'number': '#23', 'subtitle': '続・ちゃぶだい返し'},
                    {'title': 'SHIROBAKO', 'number': '#24', 'subtitle': '遠すぎた納品'}
                ]
            )
        ]
    )
    def test_overflow(self, sqs, create_sqs_queue, alert_data):
        enqueue(alert_data, create_sqs_queue, sqs)
