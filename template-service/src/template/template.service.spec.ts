import { Test, TestingModule } from '@nestjs/testing';
import { TemplateService } from './template.service';
import { getRepositoryToken } from '@nestjs/typeorm';
import { Template } from './template.entity';

describe('TemplateService', () => {
  let service: TemplateService;

  const mockTemplateRepository = {
    find: jest.fn(),
    findOne: jest.fn(),
    create: jest.fn(),
    save: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        TemplateService,
        {
          provide: getRepositoryToken(Template),
          useValue: mockTemplateRepository,
        },
      ],
    }).compile();

    service = module.get<TemplateService>(TemplateService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('findAll', () => {
    it('should return an array of templates', async () => {
      const expectedTemplates = [
        {
          id: '1',
          code: 'welcome_email',
          name: 'Welcome Email',
          subject: 'Welcome!',
          body: 'Hello {{name}}',
          type: 'email',
          language: 'en',
          version: 1,
        },
      ];
      mockTemplateRepository.find.mockResolvedValue(expectedTemplates);

      const result = await service.findAll();
      expect(result).toEqual(expectedTemplates);
      expect(mockTemplateRepository.find).toHaveBeenCalled();
    });
  });

  describe('findByCode', () => {
    it('should return a template by code', async () => {
      const expectedTemplate = {
        id: '1',
        code: 'welcome_email',
        name: 'Welcome Email',
        subject: 'Welcome!',
        body: 'Hello {{name}}',
        type: 'email',
        language: 'en',
        version: 1,
      };
      mockTemplateRepository.findOne.mockResolvedValue(expectedTemplate);

      const result = await service.findByCode('welcome_email');
      expect(result).toEqual(expectedTemplate);
      expect(mockTemplateRepository.findOne).toHaveBeenCalledWith({
        where: { code: 'welcome_email' },
      });
    });
  });

  describe('create', () => {
    it('should create and return a template', async () => {
      const createTemplateDto = {
        code: 'test_template',
        name: 'Test Template',
        subject: 'Test',
        body: 'Test body',
        type: 'email',
        language: 'en',
        version: 1,
      };
      const expectedTemplate = { id: '2', ...createTemplateDto };

      mockTemplateRepository.create.mockReturnValue(expectedTemplate);
      mockTemplateRepository.save.mockResolvedValue(expectedTemplate);

      const result = await service.create(createTemplateDto);
      expect(result).toEqual(expectedTemplate);
      expect(mockTemplateRepository.create).toHaveBeenCalledWith(
        createTemplateDto,
      );
      expect(mockTemplateRepository.save).toHaveBeenCalledWith(
        expectedTemplate,
      );
    });
  });
});
