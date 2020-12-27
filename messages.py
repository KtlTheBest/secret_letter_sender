START = "Hello and welcome to the Anonymous Secret letter sender\\.\n" + \
        "\n" + \
        "The concept of the bot is pretty simple\\. " + \
        "All you do is choose the person whom you want to send a secret message " + \
        "and then you'll just write the message to me\\.\n" + \
        "\n" + \
        "You shouldn't worry about the messages leaking somewhere \\(from the bot's side\\) \n" + \
        "Oracle has implemented an encryption mechanism " + \
        "so he wouldn't be able to read your messages\\.\n" + \
        "So feel free to use it\\. \n" + \
        "\n" + \
        "There are some restrictions, however\\. You can only message people " + \
        "who have pressed a 'start' from the bot\\. " + \
        "You'll be notified, however, if somebody connects to the bot\\. " + \
        "\\(The same goes to you and the others users know that you started using bot\\)\\." + \
        "\n" + \
        "With that being said, the bot should be intuitive to use\\. " + \
        "We're almost there\\.\n" + \
        "\n" + \
        "Please, enter your custom encryption key\\."

HELP = "Usage:\n" + \
       "/help \\- prints this usage manual\n" + \
       "/list \\- see the list of users whom you can send letters\n" + \
       "/letter \\- choose recipient and write a letter\n" + \
       "/delete \\- choose recipient and delete the letter to that person\n" + \
       "/cancel \\- Cancel the ongoing operation"

PROMPT_TO_GET_RECIPIENT = "Please, chooose the recipient from the list " + \
                          "and then we will start composing a letter\\."

PROMPT_TO_GET_LETTER = "Nice, now send me a letter as a message, that you want to send\\."

TRY_AGAIN_RECIPIENT = "Something went wrong, please try choosing the recipient again\\."

GET_MESSAGE = "Nice, I've saved your message\\. If you change your mind for some reason, " + \
              "you can delete it with a /delete command\\.\n\n" + \
              "Now, to get help, enter the /help command\\."

START_DELETE = "Okay, choose the person to whom you want to delete the letter."

NO_MESSAGES_TO_DELETE = "There are no letters to delete\\.\\.\\."

TRY_AGAIN_DELETE_RECIPIENT = "Something went wrong, please try choosing the recipient again\\."

CONFIRM_DELETE = "Are you sure that you want to delete the letter\\?"

DIDNT_DELETE = "Good\\. The message will stay until further actions"

DELETED_LETTER = "The message is deleted"
