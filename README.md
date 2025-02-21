# Texas Legislature Bill Scraping Process
This repository contains the code to scrape the Texas Legislature website for bill information. The code is written in Python and uses the BeautifulSoup library to scrape the website. The code is designed to scrape the bill information for the current legislative session.


## Interfaces
The code provides two interfaces for scraping the Texas Legislature website:

  - ### Link Builders  
  The link builders interface provides functions to generate the URLs for the Texas Legislature website. The functions generate URLs for the bill search page, the bill text page, and the bill history page. The functions take parameters such as the bill number, session, and chamber to generate the URLs.

    - #### Bases  
    This script defines an abstract base class and several utility functions to facilitate the scraping of legislative session data for the Texas Legislature. It uses the `SQLModel` library for ORM (Object-Relational Mapping), `pydantic` for data validation, and `selenium` for web scraping. The script includes the following key components:
      
      - **Utility Functions**:
        - `get_link`: Retrieves the URL of a link element based on its text.
        
        - **Dependency Injection**:
          - `configure_injection`: Configures dependency injection for `BrowserDriver` and `BrowserWait`.
        
        - **Base Classes**:
          - `DBModelBase`: A base class for database models.
          - `NonDBModelBase`: A base class for non-database models.
        
        - **Abstract Base Class**:
          - `LegislativeSessionLinkBuilder`: An abstract base class for building links related to legislative sessions. It includes methods for selecting legislative sessions, fetching data, and navigating pages.
        
        - **Methods**:
          - `LegislativeSessionLinkBuilder.driver_and_wait`: Provides a context manager for the web driver and wait.
          - `LegislativeSessionLinkBuilder.select_legislative_session`: Selects a legislative session from a dropdown.
          - `LegislativeSessionLinkBuilder._legistative_session_selector`: Helper method for selecting a legislative session.
          - `LegislativeSessionLinkBuilder._get_text_by_label`: Retrieves text by label from a web element.
          - `LegislativeSessionLinkBuilder.get_text_by_label_context`: Context manager for getting text by label.
          - `LegislativeSessionLinkBuilder.fetch`: Fetches data by navigating to a page and getting links.
          - `LegislativeSessionLinkBuilder.navigate_to_page`: Abstract method for navigating to a page.
          - `LegislativeSessionLinkBuilder.get_links`: Abstract method for getting links.


- ### Scrapers
The scrapers interface provides functions to scrape the Texas Legislature website for bill information. The functions scrape the bill information from the bill search page, the bill text page, and the bill history page. The functions take parameters such as the bill number, session, and chamber to scrape the bill information.

## Models
The code provides models to represent the bill information scraped from the Texas Legislature website. The models include classes for the bill, bill text, and bill history. The classes have attributes to store the relevant information such as the bill number, session, chamber, title, text, and history.
### Model Types
- ### Bases
The base models provide the base classes for the bill, bill text, and bill history. The base classes have attributes to store the relevant information such as the bill number, session, chamber, title, text, and history.
The `TexasLegislatureModelBase` class is the base class for all the models. It provides the base configuration for the models, such as allowing arbitrary types, validating assignments, and using enum values.
```python
class TexasLegislatureModelBase(SQLModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        use_enum_values=True,
    )
```
- ### Bills
### Script Description

This script defines several classes and functions to model and process legislative bill data for the Texas Legislature. It uses the `SQLModel` library for ORM (Object-Relational Mapping) and `pydantic` for data validation. The script includes the following key components:

- **Utility Functions**:
  - `get_element_text`: Extracts and cleans text from HTML elements.
  - `format_datetime`: Parses and formats date strings from HTML elements.
  - `check_url`: Ensures URLs use the HTTPS scheme.

- **Annotated Types**:
  - `HttpsValidatedURL`: A URL type that ensures HTTPS scheme.
  - `WebElementText`: A type for extracting text from HTML elements.
  - `WebElementDate`: A type for parsing dates from HTML elements.

- **Data Models**:
  - `BillDoc`: Represents a document related to a bill.
  - `BillCompanion`: Represents a companion bill.
  - `BillAmendment`: Represents an amendment to a bill.
  - `BillVersion`: Represents a version of a bill.
  - `BillAction`: Represents an action taken on a bill.
  - `TXLegeBill`: Represents a legislative bill with various related data such as versions, amendments, and actions.

- **Methods**:
  - `TXLegeBill.create_ids`: Generates unique IDs for the bill and its related entities.

These components work together to scrape, parse, and store legislative bill data from the Texas Legislature website. The script is designed to handle various aspects of bill data, including documents, amendments, versions, and actions, ensuring data integrity and consistency.
- ### Committees
### Script Description

This script defines several classes to model and process committee vote data for the Texas Legislature. It uses the `SQLModel` library for ORM (Object-Relational Mapping). The script includes the following key components:

- **Data Models**:
  - `CommitteeVote`: Represents a vote within a committee on a specific bill.
  - `CommitteeDetails`: Represents the details of a committee, including its votes and bills.

- **Methods**:
  - `CommitteeVote.create_id`: Generates a unique ID for the committee vote.
  - `CommitteeDetails.__hash__`: Provides a hash function for the committee details.
  - `CommitteeDetails.__repr__`: Provides a string representation for the committee details.

These components work together to model and store committee vote data from the Texas Legislature. The script is designed to handle various aspects of committee data, ensuring data integrity and consistency.
