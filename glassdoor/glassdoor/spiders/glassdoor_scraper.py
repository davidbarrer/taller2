# -*- coding: utf-8 -*-
import scrapy
import re
import glassdoor.constants as constants
import sys
from loguru import logger
from scrapy import FormRequest

logger.add(sys.stdout,
            format="<green>{time}</green><level>{message}</level>", 
            filter="parser", 
            level="INFO")

class GlassdoorScraperSpider(scrapy.Spider):
    name = 'glassdoor_scraper'
    allowed_domains = ['www.glassdoor.com']
    total_scraped_items = 0
    start_urls = ['https://www.glassdoor.com/index.htm']

    def parse(self, response):
        user_origin = response.xpath('//input[@name="userOriginHook"]/@value').get()
        yield FormRequest.from_response(response, formdata={
            'gdToken': '',
            'userOriginHook': user_origin,
            'postLoginUrl': '',
            'emailOptOut':'',
            'user.email_x': 'bglassdoor@gmail.com',
            'user.password_x': 'glassdoorbot12345'
        },callback=self.after_login)
        
    def after_login(self, response):
        urls = constants.urls
        for url in urls:
            yield scrapy.Request(url= url,callback=self.action)

    def action(self, response):
        links = response.xpath('//p[@class="m-0"]/a[contains(@href,"Front-End-Developer")'
                                + ' or contains(@href,"Backend-Developer") or contains(@href,"Devops")'
                                + ' or contains(@href,"QA-Engineering") or contains(@href,"Security-Engineer")'
                                + ' or contains(@href,"UX-Designer") or contains(@href,"UI-Designer")'
                                + ' or contains(@href,"Tester") or contains(@href,"Data-Engineer")'
                                + ' or contains(@href,"Data-Scientist") or contains(@href,"Software-Architect")]')

        currency = response.xpath('//div[@class="css-1uyte9r css-1qxtz39  nowrap col-4 '
                                + 'd-none d-md-flex flex-column align-items-end"]/text()').get().split(" ")[4]
        
        for link in links:
            job_link = link.xpath('.//@href').get()
            job_name = link.xpath('.//text()').get()
            company = response.xpath('//p[@class="m-0 "]/text()').get()
            logger.info("Started scrape on: {}",job_link)
            
            yield response.follow(url=job_link,
                                callback=self.parse_link,
                                cb_kwargs={"currency":currency,
                                        "job_name":job_name,
                                        "company":company})

        next_page = response.xpath('//a[@class="pagination__ArrowStyle__nextArrow  "]'
                                +'/@href').get()
        
        if next_page:
            yield scrapy.Request(url=next_page,callback=self.parse)

    def parse_link(self,response, currency, job_name, company):

        last_update = response.xpath('//span[@class="css-1qxtz39 css-1uyte9r"]'
                                    +'/text()').get()

        last_update = re.split(',| ',last_update)
        last_update = last_update[2] + "/" + last_update[1] + "/" + last_update[4]
        job_name = job_name
        company = company
        job_salary = response.xpath('//h2[@class="m-0" or @class="d-inline m-0' 
                                + ' css-1tx26uv"]/text()').get()

        rate = response.xpath('//div[@class="d-flex align-items-baseline"]/span'
                                +'/text()').get()
        salary_info = response.xpath('//p[@class=" css-1vkj9it"]/text()').get()
        currency = currency

        benefits_link = response.xpath('//nav[@class="dataState cell middle '
                                        +'alignRt noWrap p"]/a/@href').get()

        if benefits_link:
            yield response.follow(url=benefits_link,callback=self.parse_benefits,
                                cb_kwargs={
                                    "last_update":last_update,
                                    "job_name":job_name,
                                    "company":company,
                                    "job_salary":job_salary,
                                    "rate":rate,
                                    "currency":currency,
                                    "salary_info":salary_info})
        else:
            self.total_scraped_items += 1
            logger.info("Currently {} responses has been processed",self.total_scraped_items)
            yield {
                "last_update": last_update,
                "Job_name":job_name,
                "company":company,
                "job_salary": job_salary,
                "rate": rate,
                "currency": currency,
                "salary_info": salary_info,
                "Benefits": ""
                }


    def parse_benefits(self,response, job_name, company,
                         last_update, job_salary, rate, salary_info, currency):
        if response.status == 200:
            benefits = response.xpath('//ul/li/span[@class="SVGInline css-1cjz1oj d-flex '
                                    +'align-items-center"]//following-sibling::a/text()[position()=1]').getall()
            self.total_scraped_items += 1
            logger.info("Currently {} responses has been processed",self.total_scraped_items)
            yield {
                "last_update": last_update,
                "Job_name":job_name,
                "company":company,
                "job_salary": job_salary,
                "rate": rate,
                "currency": currency,
                "salary_info": salary_info,
                "Benefits": benefits
                }
        else:
           logger.info("Got {} response status", response.status)
           
