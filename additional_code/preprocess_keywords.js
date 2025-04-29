function preprocessKeywords() {
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = spreadsheet.getActiveSheet();
  var startRow = 1;
  var totalRows = sheet.getLastRow();
  var numRows = totalRows - startRow + 1;
  Logger.log("Processing row " + (numRows));
  var columnTitleData = sheet.getRange(startRow, 4, numRows, 1).getValues();
  var columnEData = sheet.getRange(startRow, 5, numRows, 1).getValues();
  var columnGData = sheet.getRange(startRow, 7, numRows, 1).getValues();      
  var columnHData = sheet.getRange(startRow, 8, numRows, 1).getValues(); 
  var columnCodeData = sheet.getRange(startRow, 2, numRows, 1).getValues();
  var columnArtRefData = sheet.getRange(startRow, 3, numRows, 1).getValues();
  var newSheet = spreadsheet.getSheetByName('New Test Cleaned Keywords + Paper Names + IDs');
  if (!newSheet) {
    newSheet = spreadsheet.insertSheet('New Test Cleaned Keywords + Paper Names + IDs');
    newSheet.getRange(1, 1).setValue('Year');
    newSheet.getRange(1, 2).setValue('Category');
    newSheet.getRange(1, 3).setValue('Paper Title');
    newSheet.getRange(1, 4).setValue('Keywords');
    newSheet.getRange(1, 5).setValue('Code');
    newSheet.getRange(1, 6).setValue('Article Ref');
  }
  var nextEmptyRow = newSheet.getLastRow()+1;
  for (var i = 0; i < numRows; i++) {
    var title = columnTitleData[i][0];
    var year = columnEData[i][0];
    var category = columnGData[i][0];
    var text = columnHData[i][0];
    var code = columnCodeData[i][0];
    var ref = columnArtRefData[i][0];
    Logger.log("Processing row " + (i + startRow) + ": " + title + " | Year: " + year + " | Category: " + category);
    if (typeof text === 'string' && text.trim().length > 0) {
      var cleanedKeywords = preprocessText(text);
      newSheet.getRange(nextEmptyRow, 1).setValue(String(year));
      newSheet.getRange(nextEmptyRow, 2).setValue(String(category));
      newSheet.getRange(nextEmptyRow, 3).setValue(title);
      newSheet.getRange(nextEmptyRow, 4).setValue(cleanedKeywords.join(', '));
      newSheet.getRange(nextEmptyRow, 5).setValue(String(code));
      newSheet.getRange(nextEmptyRow, 6).setValue(String(ref));
    } else {
      newSheet.getRange(nextEmptyRow, 1).setValue(String(year));
      newSheet.getRange(nextEmptyRow, 2).setValue(String(category));
      newSheet.getRange(nextEmptyRow, 3).setValue(title);
      newSheet.getRange(nextEmptyRow, 4).setValue('');
      newSheet.getRange(nextEmptyRow, 5).setValue(String(code));
      newSheet.getRange(nextEmptyRow, 6).setValue(String(ref));
    }
    nextEmptyRow++;
  }
}
function preprocessText(text) {
  var preservedPhrases = [];
  text = text.replace(/(["(].*?[")])/g, function(match) {
    preservedPhrases.push(match.trim());
    return '';
  });
  text = text.replace(/;/g, ',').replace(/[\n\t]/g, ',');
  var keywords = text.split(',').map(function(keyword) {
    keyword = keyword.trim().replace(/[^\w\s-()]/g, '');
    return keyword.toLowerCase();
  });
  var resultKeywords = keywords.filter(function(keyword) {
    return keyword.length > 0;
  }).concat(preservedPhrases);
  return resultKeywords;
}
