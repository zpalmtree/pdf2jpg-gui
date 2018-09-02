import QtQuick 2.6
import QtQuick.Window 2.2
import QtQuick.Layouts 1.11
import QtQuick.Controls 2.4
import QtQuick.Dialogs 1.3

Window {
    title: "pdf2jpg"
    visible: true

    minimumHeight: 250
    minimumWidth: 350

    ColumnLayout {
        id: columnLayout

        enabled: !manager.inProgress

        anchors.fill: parent
        anchors.margins: 10

        Label {
            Layout.alignment: Qt.AlignCenter
            text: "PDF File to convert: "
        }

        Button {
            Layout.alignment: Qt.AlignCenter
            id: filePickerButton
            Layout.fillWidth: true
            text: "Pick a PDF file"
            onClicked: filePicker.visible = true
        }

        FileDialog {
            id: filePicker
            nameFilters: [ "PDF Files (*.pdf)" ]
            selectMultiple: false
            folder: shortcuts.home
            onAccepted: filePickerButton.text = filePicker.fileUrl
        }

        Switch {
            Layout.alignment: Qt.AlignCenter
            id: multipleImages
            text: "Create an image for each page?"
        }

        Button {
            Layout.alignment: Qt.AlignCenter
            id: convertButton
            Layout.fillWidth: true
            text: "Convert"

            enabled: filePicker.fileUrl != ""

            onClicked: {
                manager.convert(filePicker.fileUrl, multipleImages.checked)
            }
        }

        ProgressBar {
            Layout.alignment: Qt.AlignCenter
            Layout.fillWidth: true
            id: conversionProgress
            indeterminate: manager.inProgress
        }

        MessageDialog {
            id: conversionDialog
            visible: manager.dialogVisible
            title: manager.dialogTitle
            text: manager.dialogText
        }
    }
}
