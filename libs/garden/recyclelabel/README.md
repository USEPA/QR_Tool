# ScrollLabel

ScrollLabel is a Kivy widget based on RecycleView and Label to display big chunk of text, without to worry about maximum texture size on mobile.
The implementation does not check for maximum texture size, as every mobile can at least display a texture equal to the size of their own screen.
The ScrollLabel size, in usage, will not be bigger than the size of the screen.

Based on that asumption, we just layout the text to get all the lines, and then display them into a RecycleView. No more black texture, and smooth text scrolling.

This widget is under heavy work and API is still uncertain. Don't use unless you like experimentation.
