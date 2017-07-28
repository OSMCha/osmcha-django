Change Log
==========

Log of changes since the version 2.0

[2.3.1] - 2017-07-28

- Disable 'cachealot' in aws-production settings
- Update osmcha lib version to 0.4.0
- Add CHANGELOG.rst

[2.3.0] - 2017-07-25

- Add 'uid' field to BlacklistedUser model
- use 'uid' instead of 'id' in BlacklistUser views
- Allow put and patch method on BlacklistedUserDetailAPIView
- Add filter by 'uid' in list changeset and feature endpoints

[2.2.1] - 2017-07-18

- Improve 'date' and 'check_date' filters to avoid XSS
- Update documentation of AOIListCreateAPIView


[2.2.0] - 2017-07-15

- Add date field to AreaOfInterest and ordering to its list endpoint


[2.1.1] - 2017-07-14

- Add number of changesets in the stats views
- Update osmcha version to 0.3.9 in requirements


[2.1.0] - 2017-07-12

- Fix changeset and feature filters inside AoI
- Adjust django swagger authentication settings


[2.0] - 2017-06-21

- A general rewrite of osmcha-django to serve data in a REST API.
