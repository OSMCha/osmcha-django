from django.test import TestCase, Client
from django.core.urlresolvers import reverse

import json

# Create your tests here.
class TestFeatureSuspicionCreate(TestCase):
    
    def setUp(self):
        self.client = Client()

    def test_suspicion_create(self):
        fixture = {
          "geometry": {
            "type": "LineString",
            "coordinates": [
              [
                41.5082139,
                52.5817404
              ],
              [
                41.5083964,
                52.5815737
              ],
              [
                41.5090171,
                52.5811133
              ],
              [
                41.5098284,
                52.5804884
              ],
              [
                41.5098657,
                52.5804596
              ],
              [
                41.5099465,
                52.5803974
              ],
              [
                41.5102895,
                52.580127
              ],
              [
                41.511222,
                52.5794008
              ],
              [
                41.5122121,
                52.5786679
              ],
              [
                41.5124606,
                52.5784839
              ],
              [
                41.5130296,
                52.5780596
              ],
              [
                41.513464,
                52.5777497
              ],
              [
                41.5135522,
                52.5776818
              ],
              [
                41.5138896,
                52.5774223
              ],
              [
                41.5147903,
                52.5767461
              ]
            ]
          },
          "type": "Feature",
          "id": "way!169218447!24",
          "properties": {
            "maxspeed": "60",
            "result:new_mapper": {
              "cfVersion": 2,
              "newMapper": 1
            },
            "name": "\\u0443\\u043b\\u0438\\u0446\\u0430 \\u041f\\u043e\\u0441\\u043a\\u043e\\u043d\\u043a\\u0438\\u043d\\u0430",
            "osm:id": 169218447,
            "oldVersion": {
              "geometry": {
                "type": "LineString",
                "coordinates": [
                  [
                    41.5082139,
                    52.5817404
                  ],
                  [
                    41.5083964,
                    52.5815737
                  ],
                  [
                    41.5090171,
                    52.5811133
                  ],
                  [
                    41.5098284,
                    52.5804884
                  ],
                  [
                    41.5098657,
                    52.5804596
                  ],
                  [
                    41.5099465,
                    52.5803974
                  ],
                  [
                    41.5102895,
                    52.580127
                  ],
                  [
                    41.511222,
                    52.5794008
                  ],
                  [
                    41.5124606,
                    52.5784839
                  ],
                  [
                    41.5130296,
                    52.5780596
                  ],
                  [
                    41.513464,
                    52.5777497
                  ],
                  [
                    41.5138896,
                    52.5774223
                  ],
                  [
                    41.5147903,
                    52.5767461
                  ]
                ]
              },
              "type": "Feature",
              "id": "way!169218447!23",
              "properties": {
                "maxspeed": "60",
                "lanes": "2",
                "name": "\\u0443\\u043b\\u0438\\u0446\\u0430 \\u041f\\u043e\\u0441\\u043a\\u043e\\u043d\\u043a\\u0438\\u043d\\u0430",
                "osm:changeset": 36640459,
                "osm:version": 23,
                "osm:type": "way",
                "osm:uid": 1781497,
                "osm:id": 169218447,
                "osm:user": "lcat",
                "osm:timestamp": 1453065048000,
                "highway": "tertiary"
              }
            },
            "osm:changeset": 42893048,
            "suspicions": [
              {
                "reason": "new mapper edits",
                "reason": "moved an object a significant amount"
              }
            ],
            "osm:type": "way",
            "osm:uid": 4173553,
            "osm:version": 24,
            "osm:user": "Victor Denisow",
            "result:name_modified": {},
            "lanes": "2",
            "highway": "tertiary",
            "osm:timestamp": 1476443255000
            }
        }
        response = self.client.post(reverse('feature:create_suspicion'), data = json.dumps(fixture), content_type="application/json")
        self.assertNotEqual(response.status_code, 400)

    def test_duplicate_suspicion_create(self):
        fixture = {
          "geometry": {
            "type": "LineString",
            "coordinates": [
              [
                41.5082139,
                52.5817404
              ],
              [
                41.5083964,
                52.5815737
              ],
              [
                41.5090171,
                52.5811133
              ],
              [
                41.5098284,
                52.5804884
              ],
              [
                41.5098657,
                52.5804596
              ],
              [
                41.5099465,
                52.5803974
              ],
              [
                41.5102895,
                52.580127
              ],
              [
                41.511222,
                52.5794008
              ],
              [
                41.5122121,
                52.5786679
              ],
              [
                41.5124606,
                52.5784839
              ],
              [
                41.5130296,
                52.5780596
              ],
              [
                41.513464,
                52.5777497
              ],
              [
                41.5135522,
                52.5776818
              ],
              [
                41.5138896,
                52.5774223
              ],
              [
                41.5147903,
                52.5767461
              ]
            ]
          },
          "type": "Feature",
          "id": "way!169218447!24",
          "properties": {
            "maxspeed": "60",
            "result:new_mapper": {
              "cfVersion": 2,
              "newMapper": 1
            },
            "name": "\\u0443\\u043b\\u0438\\u0446\\u0430 \\u041f\\u043e\\u0441\\u043a\\u043e\\u043d\\u043a\\u0438\\u043d\\u0430",
            "osm:id": 169218447,
            "oldVersion": {
              "geometry": {
                "type": "LineString",
                "coordinates": [
                  [
                    41.5082139,
                    52.5817404
                  ],
                  [
                    41.5083964,
                    52.5815737
                  ],
                  [
                    41.5090171,
                    52.5811133
                  ],
                  [
                    41.5098284,
                    52.5804884
                  ],
                  [
                    41.5098657,
                    52.5804596
                  ],
                  [
                    41.5099465,
                    52.5803974
                  ],
                  [
                    41.5102895,
                    52.580127
                  ],
                  [
                    41.511222,
                    52.5794008
                  ],
                  [
                    41.5124606,
                    52.5784839
                  ],
                  [
                    41.5130296,
                    52.5780596
                  ],
                  [
                    41.513464,
                    52.5777497
                  ],
                  [
                    41.5138896,
                    52.5774223
                  ],
                  [
                    41.5147903,
                    52.5767461
                  ]
                ]
              },
              "type": "Feature",
              "id": "way!169218447!23",
              "properties": {
                "maxspeed": "60",
                "lanes": "2",
                "name": "\\u0443\\u043b\\u0438\\u0446\\u0430 \\u041f\\u043e\\u0441\\u043a\\u043e\\u043d\\u043a\\u0438\\u043d\\u0430",
                "osm:changeset": 36640459,
                "osm:version": 23,
                "osm:type": "way",
                "osm:uid": 1781497,
                "osm:id": 169218447,
                "osm:user": "lcat",
                "osm:timestamp": 1453065048000,
                "highway": "tertiary"
              }
            },
            "osm:changeset": 42893048,
            "suspicions": [
              {
                "reason": "new mapper edits"
              }
            ],
            "osm:type": "way",
            "osm:uid": 4173553,
            "osm:version": 24,
            "osm:user": "Victor Denisow",
            "result:name_modified": {},
            "lanes": "2",
            "highway": "tertiary",
            "osm:timestamp": 1476443255000
            }
        }
        response = self.client.post(reverse('feature:create_suspicion'), data = json.dumps(fixture), content_type="application/json")
        self.assertNotEqual(response.status_code, 400)
