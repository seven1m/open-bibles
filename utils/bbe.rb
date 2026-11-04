#!/usr/bin/env ruby

# 1. download from: http://www.o-bible.com/download/bbe.gz
# 2. gunzip bbe.gz
# 3. ruby bbe.rb > ../eng-bbe.usfx.xml

require 'bundler/inline'

gemfile do
  source 'https://rubygems.org'
  gem 'builder', '~> 3.3'
end

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

lines = File.readlines('bbe', encoding: 'UTF-8')
lines.shift if lines.first&.match?(/Textfile/)
verses = lines.map do |line|
  book, reference, text = line.split(' ', 3)
  chapter, verse = reference.split(':')
  [book, chapter, verse, text.strip]
end

xml = Builder::XmlMarkup.new(target: $stdout)
xml.instruct! :xml, version: '1.0', encoding: 'UTF-8'
xml.usfx('xmlns:xsi' => 'http://eBible.org/usfx.xsd', 'xsi:noNamespaceSchemaLocation' => 'usfx.xsd') do
  xml.languageCode 'eng'
  verses.slice_when { |a, b| a[0] != b[0] }.each_with_index do |book_verses, index|
    book_id, book_name = BOOKS.to_a.fetch(index)
    xml.book(id: book_id) do
      xml.id 'Bible in Basic English (BBE)', id: book_id
      xml.ide charset: 'UTF-8'
      xml.h book_name
      book_verses.slice_when { |a, b| a[1] != b[1] }.each do |chapter_verses|
        xml.c id: chapter_verses.first[1]
        xml.p do
          chapter_verses.each do |_, _, verse, text|
            xml.v id: verse
            xml.text! text
            xml.ve
          end
        end
      end
    end
  end
end
