Feature: Login
  Users must authenticate before they can shop.

  Scenario: Successful login with valid credentials
    Given I am on the login page
    When I log in as "standard_user" with password "Shop-Test#2026"
    Then I should see the products page

  Scenario Outline: Login is rejected for invalid credentials
    Given I am on the login page
    When I log in as "<username>" with password "<password>"
    Then I should see the error "<message>"

    Examples:
      | username        | password     | message                                                     |
      | standard_user   | wrong_pw     | Username and password do not match any user in this service |
      | unknown_user    | Shop-Test#2026 | Username and password do not match any user in this service |
      | locked_out_user | Shop-Test#2026 | Sorry, this user has been locked out.                       |
