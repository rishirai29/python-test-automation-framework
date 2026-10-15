Feature: Orders API
  Authenticated users can place orders; stock is enforced.

  Scenario: Place an order as an authenticated user
    Given I am authenticated as "standard_user" via the API
    When I order 2 units of product 1
    Then the response status is 201
    And the order status is "CREATED"
    And the stock of product 1 is 8 in the database

  Scenario: Ordering more than the available stock fails
    Given I am authenticated as "standard_user" via the API
    When I order 99 units of product 4
    Then the response status is 409
