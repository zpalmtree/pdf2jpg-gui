import os
import uuid

from wand.image import Image as Img
from wand.exceptions import DelegateError

from PIL import Image

from PySide2.QtGui import QGuiApplication
from PySide2.QtQml import QQmlApplicationEngine
from PySide2.QtCore import Slot, QObject, Signal, Property

from threading import Thread

import sys

COMPRESSION_QUALITY = 99
IMAGE_RESOLUTION = 200


def pdfToJpegMultipleFiles(inputFile, outputFile):
    try:
        with Img(filename=inputFile, resolution=IMAGE_RESOLUTION) as input:
            if input.format != 'PDF':
                raise RuntimeError('Input file is not a PDF.')

            input.compression_quality = COMPRESSION_QUALITY

            input.save(filename=outputFile)

    # If the pdf is corrupt / empty, it will attempt to free the image object
    # when we exit the program, and this fails because the image object is
    # empty. This also can't be caught because it occurs when the runtime is
    # exiting, so we'll get an ugly stack trace when we quit. We can't attempt
    # to del it before exiting because this will fail, so it will again be
    # automatically called on exit.
    except DelegateError:
        raise RuntimeError('PDF file appears corrupted.')


def pdfToJpegSingleFile(inputFile, outputFile):
    imageFiles = []

    try:
        with Img(filename=inputFile, resolution=IMAGE_RESOLUTION) as input:
            if input.format != 'PDF':
                raise RuntimeError('Input file is not a PDF.')

            input.compression_quality = COMPRESSION_QUALITY

            # The API to split a file into sections and combine them natively
            # appears to not work and crash with a null insertion, so instead
            # lets reopen the written files and combine them with pillow...
            u = uuid.uuid4()

            # Get the directory the output file is in
            directory = os.path.dirname(outputFile)

            # Get the name of the output file, without the full path
            basename = os.path.basename(outputFile)

            # Make our tmpFileName
            tmpFileName = directory + '/' + str(u) + '-' + basename

            # Save the output file
            input.save(filename=tmpFileName)

            # List each file, take the ones which start with the uuid,
            # then turn it into an absolute path
            imageFiles = [os.path.abspath(os.path.join(directory, filename))
                          for filename in os.listdir(directory)
                          if filename.startswith(str(u))]

            imageFiles.sort()

            # Need to make a list as maps can only be iterated over once
            images = list(map(Image.open, imageFiles))

            # Get the widths and heights for each individual image
            widths, heights = zip(*(i.size for i in images))

            # Each image laid end to end gives us the height
            imgHeight = sum(heights)

            # And the width is the width of the largest image
            imgWidth = max(widths)

            # Make our output image
            outputImage = Image.new('RGB', (imgWidth, imgHeight))

            heightOffset = 0

            # Loop through each image, and append it to the output,
            # altering the height offset by the height of each image as we
            # go
            for image in images:
                outputImage.paste(image, (0, heightOffset))
                heightOffset += image.size[1]

            outputImage.save(outputFile)

    # If the pdf is corrupt / empty, it will attempt to free the image object
    # when we exit the program, and this fails because the image object is
    # empty. This also can't be caught because it occurs when the runtime is
    # exiting, so we'll get an ugly stack trace when we quit. We can't attempt
    # to del it before exiting because this will fail, so it will again be
    # automatically called on exit.
    except DelegateError:
        raise RuntimeError('PDF file appears corrupted.')

    # Make sure we remove the tmp files
    finally:
        for file in imageFiles:
            os.remove(file)


class Manager(QObject):
    inProgressChanged = Signal()

    def __init__(self):
        QObject.__init__(self)
        self._inProgress = False
        self._dialogVisible = False
        self._dialogTitle = ""
        self._dialogText = ""

    def doConvert(self, inputFile, multipleImages):
        # Strip the file:// prefix qml adds, if present
        if inputFile.startswith('file://'):
            inputFile = inputFile[len('file://'):]

        # Get the output filename by replacing pdf extension with jpg
        outputFile = os.path.splitext(inputFile)[0] + '.jpg'

        try:
            if multipleImages:
                pdfToJpegMultipleFiles(inputFile, outputFile)
            else:
                pdfToJpegSingleFile(inputFile, outputFile)

            self.displayDialog('Conversion complete!',
                               'The conversion completed successfully.\nThe '
                               'output file(s) are in the same folder as the '
                               'original PDF.')

        except RuntimeError as e:
            self.displayDialog('Failed to convert PDF!',
                               'The conversion failed: ' + e)

    @Slot(str, bool)
    def convert(self, inputFile, multipleImages):
        # Let the qml know we're converting
        # self.__filename = True
        self.inProgress = True

        # Launch in a thread to not block the UI
        Thread(target=self.doConvert, args=(inputFile, multipleImages)).start()

    def displayDialog(self, title, message):
        # Re-enable UI
        self.inProgress = False

        # Set message values
        self.dialogTitle = title
        self.dialogText = message

        # Display message
        self.dialogVisible = True

    # The inProgress signal disables the UI whilst conversion is going on,
    # and enables a progress bar
    def setInProgress(self, val):
        self._inProgress = val
        self.onInProgress.emit()

    def getInProgress(self):
        return self._inProgress

    onInProgress = Signal()

    inProgress = Property(bool, getInProgress, setInProgress,
                          notify=onInProgress)

    # This signal shows the completion dialog
    def setDialogVisible(self, val):
        self._dialogVisible = val
        self.onDialogVisible.emit()

    def getDialogVisible(self):
        return self._dialogVisible

    onDialogVisible = Signal()

    dialogVisible = Property(bool, getDialogVisible, setDialogVisible,
                             notify=onDialogVisible)

    # This signal sets the dialog title
    def setDialogTitle(self, val):
        self._dialogTitle = val
        self.onDialogTitle.emit()

    def getDialogTitle(self):
        return self._dialogTitle

    onDialogTitle = Signal()

    dialogTitle = Property(str, getDialogTitle, setDialogTitle,
                           notify=onDialogTitle)

    # This signal sets the dialog text
    def setDialogText(self, val):
        self._dialogText = val
        self.onDialogText.emit()

    def getDialogText(self):
        return self._dialogText

    onDialogText = Signal()

    dialogText = Property(str, getDialogText, setDialogText,
                          notify=onDialogText)


def main():
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    manager = Manager()

    ctx = engine.rootContext()
    ctx.setContextProperty("manager", manager)

    engine.load('view.qml')

    win = engine.rootObjects()[0]
    win.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
