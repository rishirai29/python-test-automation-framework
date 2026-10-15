Feature: Shopping cart and checkout
  A logged-in user can build a cart and place an order.

  Background:
    Given I am logged in as "standard_user"

  Scenario: Add a product to the cart
    When I add product 1 to the cart
    Then the cart badge shows 1

  Scenario: Add several products to the cart
    When I add product 1 to the cart
    And I add product 2 to the cart
    And I add product 3 to the cart
    Then the cart badge shows 3

  Scenario: Remove a product from the cart
    Given I have added product 1 to the cart
    When I remove product 1 from the cart
    Then the cart badge is not shown

  Scenario: Complete a checkout
    Given I have added product 1 to the cart
    When I check out
    Then I should see the order confirmation
    And an order exists in the database for "standard_user"
