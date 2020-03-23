Change Log
==========

Log of changes since the 2.0 version

Check https://github.com/willemarcel/osmcha-django/releases for recent updates.

[4.0.0] - 2018-10-18

- Change feature model to be a JSONField of the Changeset Model
- Implement GDPR changes

[3.0.4] - 2018-06-29

- Fix error in changeset comments when it has special characters

[3.0.3] - 2018-06-18

- Update osmcha lib version to 0.4.8

[3.0.2] - 2018-06-05

- Update Django version to 2.0.6

[3.0.1] - 2018-06-04

- Replace oauth2 by requests_oauthlib

[3.0.0] - 2018-05-30

- Update Django to 2.0.4
- Update all requirements
- Remove unneeded dependencies

[2.7.5] - 2018-04-02

- Update social-core-auth to fix bug in authentication

[2.7.4] - 2018-04-02

- Update osmcha lib version
- Use https on OSM.org API requests
- Use SQL command instead of Django ORM in merge_reasons command

[2.7.3] - 2018-03-26

- Add 'merge_reasons' management command

[2.7.2] - 2018-03-12

- Update all dependencies, except Django 2.0
- Update osmcha lib to 0.4.6

[2.7.1] - 2018-02-07

- Fix encoding bugs in ChangesetCommentAPIView

[2.7.0] - 2018-02-01

- Disable automatic comments
- Add endpoint to allow user to post comments to changesets from inside OSMCha
- Modify user model to include message_good, message_bad and comment_feature fields

[2.6.0] - 2017-12-27

- Post a comment to OSM Changeset page when a review is added to a changeset (to use it, set the ENV variable ``DJANGO_ENABLE_CHANGESET_COMMENTS`` to True)
- Return the correct username of users in views

[2.5.0] - 2017-10-09

- Change license to BSD 2-Clause

[2.4.0] - 2017-10-02

- Handle errors when trying to create a duplicated UserWhitelist using the API
- Add 'whitelists' field to User detail endpoint

[2.3.9] - 2017-09-15

- Update osmcha lib to 0.4.3 and django-extensions

[2.3.8] - 2017-09-06

- Update django and psycopg

[2.3.7] - 2017-08-30

- Update osmcha lib to 0.4.2
- Add filter and ordering by number of Suspicion Reasons

[2.3.6] - 2017-08-29

- Update osmcha lib to 0.4.1
- Update Django Rest Framework to 3.6.4
- Documentation updates
- Hide features that doesn't have visible SuspicionReasons (to non staff users and only in the changesets endpoints)

[2.3.5] - 2017-08-09

- Disable SessionAuthentication in DRF endpoints

[2.3.4] - 2017-08-08

- General update of dependencies

[2.3.3] - 2017-08-05

- Update django version to 1.11.4
- Update documentation

[2.3.2] - 2017-07-28

- Update django version to 1.11.3
- Add RSS feed to list the changesets that matches an Area of Interest
- Add changeset_checked and changeset_ids filter to FeatureFilter
- Improve views and filter documentation
- Change date and check_date filters to accept datetime values

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
