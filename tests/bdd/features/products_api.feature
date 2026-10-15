Feature: Products API
  The catalogue is available over REST.

  Scenario: List all products
    When I request the product list
    Then the response status is 200
    And the response contains 6 products

  Scenario: Get a single product
    When I request product 4
    Then the response status is 200
    And the product name is "Fleece Jacket"

  Scenario: Unknown product returns not found
    When I request product 999
    Then the response status is 404
