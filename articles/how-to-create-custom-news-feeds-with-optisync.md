# How to Create Custom News Feeds with  OptiSync

### In this article, we will cover OptiSigns’ ability to create custom news apps using the OptiSync feature.

- [SharePoint News Examples](#Examples)
- [How to Set Up a Custom News Feed](#Setup)
  - [Step 1: Setting Up an API Gateway (SharePoint Example)](#Gateway)
    - [Choosing the Correct URL Endpoint for Connection](#Endpoint)
    - [SharePoint API Authentication using OAuth 2.0 in Microsoft Azure](#Authentication)
  - [Step 2: Mapping the API to a DataSource](#DataSource)
  - [Step 3: Creating a News Feed Using Designer](#Designer)
    - [Element Mapping](#Element)
  - [Applying Filters to Customize Which News Stories to Display](#Filters)

It is common for companies to share their internal communications, including memos, news, announcements and more via intranet. Digital signage will heighten employee awareness of published company news and announcements.

Using OptiSync, it’s possible to create a custom news app to display company news stored on your company’s intranet. This is achieved by connecting an intranet API with OptiSync and choosing what data to display in the [OptiSigns Designer app](https://support.optisigns.com/hc/en-us/articles/4404151402899-How-to-use-OptiSigns-Template-Designer-app-to-make-your-Digital-Signs-in-minutes).

Creating news feeds with OptiSync has a key advantage: you have full control of the look and feel of your feed. You can create feeds that match your company branding and design guidelines no matter which news source you use. We will be using SharePoint here as an example, but you can use anything that can be input as a Datasource.

Before we get started, it will be helpful to familiarize yourself with a few other concepts which will be important to understand that we cover in other articles:

- [How to Integrate API and Publish API Data via OptiSync](https://support.optisigns.com/hc/en-us/articles/22875592994195-How-to-Integrate-API-and-Publish-API-Data-via-OptiSync)
- [How to Set Up Dynamic Data Mapping via OptiSync](https://support.optisigns.com/hc/en-us/articles/29217646663187-How-to-Set-Up-Dynamic-Data-Mapping-with-OptiSync)

The API article in particular will provide detailed instructions for how to pair an API and get its data on screen with automatic updates. Once you’ve got your API set up and its data saved as a data source, you can create some of the examples below using the Designer app.

The main example tackled in this article will be company news, but this feature can be used for far more, including:

- Custom RSS feeds
- Custom XML/JSON feeds
- Inventory management systems
- Point-of-sales updates across multiple locations
- Additional internal communications
- Other news sites

---

## SharePoint News Examples

Below are some examples using SharePoint. There are numerous possibilities of how to design and create engaging news feeds using SharePoint news or other intranet applications.

Here are a few examples:

#### Bulletin Feed

![bulletin news feed example](https://support.optisigns.com/hc/article_attachments/35337756491283)

This style allows several news stories to be shown at once. The images and text are taken directly from the data source and displayed using OptiSync. These are set to periodically update every 30 minutes.

#### Single Story Feed

![single story news feed example](https://support.optisigns.com/hc/article_attachments/35337746485139)

This style allows a single story to be featured. Using Repeater settings, this will allow a rotating slate of featured news articles.

---

## How to Set Up a Custom News Feed

In order to set up a custom news feed, you'll need to follow these steps:

1. Set Up the Custom API Gateway
2. Map the API to a DataSource within OptiSigns
3. Create a News Feed Using OptiSigns Designer

### Step 1: Setting Up a Custom API Gateway (SharePoint Example)

We cover most of the details of this step in our [How to Integrate API and Publish API Data via OptiSync](https://support.optisigns.com/hc/en-us/articles/22875592994195-How-to-Integrate-API-and-Publish-API-Data-via-OptiSync) guide. Please see that guide for a step-by-step process.

However, there are a few elements which are specific to connecting to a SharePoint API (or a variety of resources in Microsoft 365), which we will cover here.

#### Choosing the Correct URL Endpoint for SharePoint Connection

There are numerous options for connecting to SharePoint’s API endpoints, and making sure you have the correct one is critical for importing the correct data into OptiSigns. Click here to learn more about [Determine SharePoint REST service endpoint URIs](https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/determine-sharepoint-rest-service-endpoint-uris?tabs=http).

For the purposes of this example, we’ll be using “Site” feature area, meaning the access point will be:

```
https://{site_url}/_api/site
```

#### SharePoint API Authentication using OAuth 2.0 in Microsoft Azure

Authentication for SharePoint can be carried out using different methods, but OAuth 2.0 has become the recommended standard. To get started using OAuth 2.0, you’ll need to [register your application in Azure Active Directory](https://learn.microsoft.com/en-us/azure/healthcare-apis/register-application).

Once that's done, you'll need:

- [**Client ID**](https://learn.microsoft.com/en-us/azure/healthcare-apis/register-application#application-id-client-id)
- [**Client Secret Value**](https://learn.microsoft.com/en-us/azure/healthcare-apis/register-application#certificates--secrets)

These are required for authentication. Any further authentication can be done in the Pre-Request stage to obtain access tokens. These authentication tokens will need to be kept refreshed: see [Microsoft's article on identity platform certificate credentials](https://learn.microsoft.com/en-us/entra/identity-platform/certificate-credentials) for more information.

When paired with an “Accept” value, this will provide authentication for your API request. You’ll need the following values:

```
Authorization: "Bearer " + accessToken  
Accept: "application/json;odata=verbose"
```

These values should be input under the **Header** tab when setting up your API request:

![api gateway header tab](https://support.optisigns.com/hc/article_attachments/35337756499091)

Be sure to **Enable this Request** before moving to the next step.

![api gateway enable this request](https://support.optisigns.com/hc/article_attachments/35337746496019)

### Step 2: Mapping the API to a DataSource

We cover most of the details of this step in our [How to Set Up Dynamic Data Mapping via OptiSync](https://support.optisigns.com/hc/en-us/articles/29217646663187-How-to-Set-Up-Dynamic-Data-Mapping-with-OptiSync). If imported correctly, your data will appear in JSON format, like this:

![json data map optisigns](https://support.optisigns.com/hc/article_attachments/35337756509075)

Your news stories will have similar data sets if you’re following this guide. The most important data fields are:

- “Title”
- “Description”
- “Banner Image URL”
  - Inputting this URL will display the banner image.

|  |
| --- |
| **NOTE** |
| You will also want to make note of the “PromotedState” data value. These will be useful for applying filters later on. Other values can also be made use of with Filters, should you so desire. |

### Step 3: Creating a News Feed Using Designer in OptiSigns

The next step is getting these values onto your screens and make them automatically update.

To get started, find your design or create a new one in the **Files/Assets** tab.

With the design open, click **"DataSource"** in the left hand column. Then, click **"Add DataSource"** to add an API data source to the design.

![firefox_ZFaS9dNCeY.jpg](https://support.optisigns.com/hc/article_attachments/43089455677587)

Scroll down to where it says **"API Gateway"** and click it.

![api gateway datasource](https://support.optisigns.com/hc/article_attachments/35337746511251)

You can also set up a multi-time Gateway with the *API Gateway Collection****.*** For this example, we’ll stick with the single-use API Gateway.

You should see this screen:

![api datasource ui optisigns](https://support.optisigns.com/hc/article_attachments/35337756519187)

- **Name -** The name of the DataSource. This is internally facing and will not be shown on your screens.
- **Select APIs -** Here you'll select from the API Gateways you've already set up in earlier steps. You can select just one, or multiple. If multiple are selected, the API DataSource will automatically aggregate them.
- **Update Interval -** How often to send requests back to the API for updates. Select from None (never call the API back), 30 minutes, 60 minutes, or every 6 hours. If you Enable WebHook on your API Request and input the provided URL in your API, this Update Interval will change to near real-time.

Hit **Save**, and the DataSource is created.

It should appear in the left column under **"Used in this design".** It will definitely appear in the **"Other DataSources"** section. You may need to refresh the page for it to appear.

![datasource sharepoint news demo example](https://support.optisigns.com/hc/article_attachments/35337746518163)

#### Element Mapping

Now that you've got your API DataSource has been created, we're ready to map the data. In this example, we will show you how to make a SharePoint News feed.

##### Adding Text Elements to a Digital Menu Board

First, create your design. You can make use of one of our repeater templates, or make the design yourself. Our repeater templates can be customized to fit in with your company branding.

![custom news feed with text elements](https://support.optisigns.com/hc/article_attachments/35337756524691)

The easiest way to set up a Custom News feed is with a **Data Repeater**. For a full breakdown of a Repeater's capabilities, [see this article](https://support.optisigns.com/hc/en-us/articles/29217646663187). Here, we'll stick to teaching how to add information from your API.

To set up a Repeater, click **"Repeaters" → Add Blank Repeater**.

![ShareX_gnoDiLL4vn.jpg](https://support.optisigns.com/hc/article_attachments/43089455679123)

With the Repeater selected, click **Settings**. A new pane will open up on the right. Here, select **Connect to DataSource**.

![firefox_Y7ut4qGqj7.jpg](https://support.optisigns.com/hc/article_attachments/43089455679763)

Select the DataSource you set up in the last set under **"Other DataSources"**.

You'll be taken back to the last pane with your DataSource now selected. Now, click **Edit** or double click the selected Repeater to head to the Repeater Editor. This is like a design-within-a-design, specifically for your Repeater (news) items. With text selected, click the arrow on the left.

![firefox_6lEOTf7EZu.jpg](https://support.optisigns.com/hc/article_attachments/43089455680531)

That brings up the DataSource tab. Click on the DataSource Used in this Design and you'll see something like this:

![firefox_0ZMcdeWGwF.jpg](https://support.optisigns.com/hc/article_attachments/43089455681043)

In this example, we want to display the title of the piece, its associated imagery, and the story itself.

By creating text and dragging data points to it, we can create a news feed like this:

![example news feed](https://support.optisigns.com/hc/article_attachments/35337756558355)

This was created by finding data points from the API and dragging them into the desired text boxes. In this case, we only wish to display the "Title,” “Banner URL Image,” and "Description" so those values were dragged into a blank or existing text box.

The value of a repeater is that it will copy the format of this one cell, then replace the data points with others from your API. It will pull as many data points as you have set up on your API. In this example, we’ve featured only one news story. The repeater will rotate through the rest, displaying only one at a time. If you want to display more, the number of repeated items and their formatting can be changed using these options under **Settings:**

![firefox_9ieNkZ0FYJ.jpg](https://support.optisigns.com/hc/article_attachments/43089441903379)

If we change the total items to, say, 3, we can get a news feed like this with a little bit of design work:

![three story news feed example](https://support.optisigns.com/hc/article_attachments/35337746553235)

Hopefully this is an effective demonstration of some of OptiSync’s abilities.

### Applying Filters to Customize Which News Stories to Display

What news stories you wish to display may vary depending on a number of factors. In order to filter out undesired or redundant stories, you can make use of the OptiSigns **DataSource** **Filter**.

To get started, highlight the data you want to filter, then hit **Settings.** Next, hit the **Filter** option under your DataSource.

![firefox_yyCyvxGXBi.jpg](https://support.optisigns.com/hc/article_attachments/43089441904659)

This screen will appear:

![firefox_M6EvhPuhbI.jpg](https://support.optisigns.com/hc/article_attachments/43089441904915)

What follows is, essentially, an [AND statement](https://support.microsoft.com/en-us/office/and-function-5f19b2e8-e1df-4408-897a-ce285a19e9d9) or an [OR statement](https://support.microsoft.com/en-us/office/and-function-5f19b2e8-e1df-4408-897a-ce285a19e9d9) you might use in Excel or Google Sheets. The easiest way to understand the Filter option is as an Excel or Google Sheet formula you input within OptiSigns.

You can add **Rules** or **RuleSets** to your filter to create as much complexity as you need:

![datasource filter option rulesets](https://support.optisigns.com/hc/article_attachments/35337756575507)

In order to set up a Rule, you’ll need to configure three values.

Selecting the first box gives you these options:

![filter first box options](https://support.optisigns.com/hc/article_attachments/35337756579731)

By default, these options equate to the **headers of the data mapped to the source.** This list will vary in length depending on how many headers you have. You can also input any value you wish by typing it in the box.

The second box is your **Variable.** OptiSigns provides these options:

![filter variable data](https://support.optisigns.com/hc/article_attachments/35337746579347)

The final option provides the following default values:

![filter final options](https://support.optisigns.com/hc/article_attachments/35337756591251)

By default, these map to a screen or other device, allowing your filter to target only certain screens.

However, this value **can be changed to anything you want.** Simply type any value you wish.

There are dozens of possibilities using the OptiSync filter to show even more precise automated data on your screens.

|  |
| --- |
| **TIP** |
| Remember the “PromotedState” data value from before? If you want to make sure only custom news articles appear on your screen, try setting the Filter to state:  **PromotedState - Equals - 2**  This should filter out any other pieces of data received from the API. |

### That’s all!

OptiSigns is the leader in [digital signage software](https://www.optisigns.com/). If you have any additional questions, concerns or any feedback about OptiSigns, feel free to reach out to our support team at [support@optisigns.com](mailto:support@optisigns.com).

---
*Article URL: https://support.optisigns.com/hc/en-us/articles/35337746613139-How-to-Create-Custom-News-Feeds-with-OptiSync*
*Article ID: 35337746613139*
*Last Updated: 2025-07-18T15:18:02Z*
