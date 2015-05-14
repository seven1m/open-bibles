require 'fileutils'
require 'nokogiri'
require 'builder'

BOOKS = {
  'MAT' => 'ᎣᏍᏛ ᎧᏃᎮᏛ ᎹᏚ ᎤᏬᏪᎳᏅᎯ',
  'MRK' => 'ᎣᏍᏛ ᎧᏃᎮᏛ ᎹᎦ ᎤᏬᏪᎳᏅᎯ',
  'LUK' => 'ᎣᏍᏛ ᎧᏃᎮᏛ ᎷᎦ ᎤᏬᏪᎳᏅᎯ',
  'JHN' => 'ᎣᏍᏛ ᎧᏃᎮᏛ ᏣᏂ ᎤᏬᏪᎳᏅᎯ',
  'ACT' => 'ᎨᏥᏅᏏᏛ ᏄᎾᏛᏁᎵᏙᎸᎢ',
  'ROM' => 'ᏉᎳ ᎶᎻ ᎠᏁᎯ ᏧᏬᏪᎳᏁᎸᎯ',
  '1CO' => 'ᎪᎵᏂᏗᏱ ᎠᏁᎯ ᎢᎬᏱᏱ ᎨᎪᏪᎳᏁᎸᎯ',
  '2CO' => 'ᎪᎵᏂᏗᏱ ᎠᏁᎯ ᏔᎵᏁ ᎨᎪᏪᎳᏁᎸᎯ',
  'GAL' => 'ᏉᎳ ᎨᎴᏏᏱ ᎠᏁᎯ ᏧᏬᏪᎳᏁᎸᎯ',
  'EPH' => 'ᏉᎳ ᎡᏈᏌ ᎠᏁᎯ ᏧᏬᏪᎳᏁᎸᎯ',
  'PHP' => 'ᏉᎳ ᏈᎵᎩᏱ ᎠᏁᎯ ᏧᏬᏪᎳᏁᎸᎯ',
  'COL' => 'ᏉᎳ ᎪᎶᏏ ᎠᏁᎯ ᏧᏬᏪᎳᏁᎸᎯ',
  '1TH' => 'ᏉᎳ ᏕᏏᎶᏂᎦ ᎠᏁᎯ ᎢᎬᏱᏱ ᏧᏬᏪᎳᏁᎸᎯ',
  '2TH' => 'ᏉᎳ ᏕᏏᎶᏂᎦ ᎠᏁᎯ ᏔᎵᏁ ᏧᏬᏪᎳᏁᎸᎯ',
  '1TI' => 'ᏉᎳ ᏧᏬᏪᎳᏅᎯ ᎢᎬᏱᏱ ᏗᎹᏗ ᏧᏬᏪᎳᏁᎸᎯ',
  '2TI' => 'ᏉᎳ ᏧᏬᏪᎳᏅᎯ ᏔᎵᏁ ᏗᎹᏗ ᏧᏬᏪᎳᏁᎸᎯ',
  'TIT' => 'ᏉᎳ ᏓᏓᏏ ᎤᏬᏪᎳᏁᎸᎯ',
  'PHM' => 'ᏉᎳ ᏆᎵᎹᏂ ᎤᏬᏪᎳᏁᎸᎯ',
  'HEB' => 'ᏉᎳ ᎠᏂᏈᎷ ᏧᏬᏪᎳᏁᎸᎯ',
  'JAS' => 'ᏥᎻ ᎤᏬᏪᎳᏅᎯ',
  '1PE' => 'ᏈᏓ ᎢᎬᏱᏱ ᎤᏬᏪᎳᏅᎯ',
  '2PE' => 'ᏈᏓ ᏔᎵᏁ ᎤᏬᏪᎳᏅᎯ',
  '1JN' => 'ᏣᏂ ᎢᎬᏱᏱ ᎤᏬᏪᎳᏅᎯ',
  '2JN' => 'ᏣᏂ ᏔᎵᏁ ᎤᏬᏪᎳᏅᎯ',
  '3JN' => 'ᏣᏂ ᏦᎢᏁ ᎤᏬᏪᎳᏅᎯ',
  'JUD' => 'ᏧᏓᏏ ᎤᏬᏪᎳᏅᎯ',
  'REV' => 'ᏣᏂ ᏄᏍᏛ ᎠᏥᎾᏄᎪᏫᏎᎸᎢ'
}

BOOKS_BY_NUM = [nil] + BOOKS.keys

unless File.exist?('tmp/cherokee')
  FileUtils.mkdir_p('tmp/cherokee')
  (1..27).each do |book_num|
    url = format('http://www.cherokeenewtestament.com/%02d.html', book_num)
    `wget -r -nH -l 1 -P tmp/cherokee/ #{url}`
  end
end

builder = Builder::XmlMarkup.new
builder.instruct!(:xml, version: '1.0', encoding: 'UTF-8')

verses = {}

Dir['tmp/cherokee/*.html'].to_a.sort.each do |filename|
  next if filename =~ /\/\d\d\.html/
  doc = Nokogiri::HTML(File.read(filename))
  doc.css('table').each do |verse|
    nums = verse.css('tr th a').first.attributes['href'].value.split('.').first
    bn, cn, vn = nums.each_char.each_slice(2).map { |n| n.join.to_i }
    cherokee = verse.css('tr th')[2]
    text = cherokee.text.sub(/\t$/, '')
    verses[bn] ||= {}
    verses[bn][cn] ||= {}
    verses[bn][cn][vn] = text
  end
end

xml = builder.usfx('xmlns:xsi' => 'http://eBible.org/usfx.xsd', 'xsi:noNamespaceSchemaLocation' => 'usfx.xsd') do |usfx|
  verses.each do |bn, chapters|
    book_id = BOOKS_BY_NUM[bn]
    usfx.book(id: book_id) do |book|
      book.h(BOOKS[book_id])
      chapters.each do |cn, verses|
        book.c(id: cn)
        verses.each do |vn, text|
          book.v(id: vn)
          book << text
          book.ve
        end
      end
    end
  end
end

puts xml
