#!/usr/bin/env ruby

# 1. download from: http://www.o-bible.com/download/bbe.gz
# 2. gunzip bbe.gz
# 3. ruby bbe.rb > ../eng-bbe.usfx.xml

BOOKS = {
  'GEN' => 'Genesis',			
  'EXO' => 'Exodus',			
  'LEV' => 'Leviticus',			
  'NUM' => 'Numbers',			
  'DEU' => 'Deuteronomy',			
  'JOS' => 'Joshua',			
  'JDG' => 'Judges',			
  'RUT' => 'Ruth',			
  '1SA' => '1 Samuel',			
  '2SA' => '2 Samuel',			
  '1KI' => '1 Kings',			
  '2KI' => '2 Kings',			
  '1CH' => '1 Chronicles',			
  '2CH' => '2 Chronicles',			
  'EZR' => 'Ezra',			
  'NEH' => 'Nehemiah',			
  'EST' => 'Esther',
  'JOB' => 'Job',			
  'PSA' => 'Psalms',			
  'PRO' => 'Proverbs',			
  'ECC' => 'Ecclesiastes',			
  'SNG' => 'Song of Songs',			
  'ISA' => 'Isaiah',			
  'JER' => 'Jeremiah',			
  'LAM' => 'Lamentations',			
  'EZK' => 'Ezekiel',			
  'DAN' => 'Daniel',
  'HOS' => 'Hosea',			
  'JOL' => 'Joel',			
  'AMO' => 'Amos',			
  'OBA' => 'Obadiah',			
  'JON' => 'Jonah',			
  'MIC' => 'Micah',			
  'NAM' => 'Nahum',			
  'HAB' => 'Habakkuk',			
  'ZEP' => 'Zephaniah',			
  'HAG' => 'Haggai',			
  'ZEC' => 'Zechariah',			
  'MAL' => 'Malachi',			
  'MAT' => 'Matthew',			
  'MRK' => 'Mark',			
  'LUK' => 'Luke',			
  'JHN' => 'John',			
  'ACT' => 'Acts',			
  'ROM' => 'Romans',			
  '1CO' => '1 Corinthians',			
  '2CO' => '2 Corinthians',			
  'GAL' => 'Galatians',			
  'EPH' => 'Ephesians',			
  'PHP' => 'Philippians',			
  'COL' => 'Colossians',			
  '1TH' => '1 Thessalonians',			
  '2TH' => '2 Thessalonians',			
  '1TI' => '1 Timothy',			
  '2TI' => '2 Timothy',			
  'TIT' => 'Titus',			
  'PHM' => 'Philemon',			
  'HEB' => 'Hebrews',			
  'JAS' => 'James',			
  '1PE' => '1 Peter',			
  '2PE' => '2 Peter',			
  '1JN' => '1 John',			
  '2JN' => '2 John',			
  '3JN' => '3 John',			
  'JUD' => 'Jude',			
  'REV' => 'Revelation',			
}

book = nil
book_num = 0
chapter = nil
lines = File.read('bbe').each_line.to_a
lines.shift if lines.first =~ /Textfile/

puts %(<?xml version="1.0" encoding="UTF-8"?><usfx xmlns:xsi="http://eBible.org/usfx.xsd" xsi:noNamespaceSchemaLocation="usfx.xsd"><languageCode>eng</languageCode>)

lines.each do |line|
  (b, r, text) = line.split(' ', 3)
  (c, v) = r.split(':')
  if b != book
    book = b
    book_id = BOOKS.keys[book_num]
    book_name = BOOKS[book_id]
    chapter = nil
    puts %(<book id="#{book_id}"><id id="#{book_id}">Bible in Basic English (BBE)</id><ide charset="UTF-8"/><h>#{book_name}</h>)
    book_num += 1
  end
  if c != chapter
    chapter = c
    puts %(<c id="#{chapter}"/><p>)
  end
  puts %(<v id="#{v}"/>#{text.strip}<ve/>)
end
